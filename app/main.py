"""Main FastAPI application."""

import json
import queue
import threading

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from app.agent import run_agent
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="0.1.0",
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    used_tools: list[str] = []
    weather_location: str | None = None


@app.get("/")
async def root():
    return {"message": "Welcome to Basic AI Agent", "app_name": settings.app_name}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = run_agent(request.message)
    return ChatResponse(
        answer=result["answer"],
        used_tools=result.get("used_tools", []),
        weather_location=result.get("weather_location"),
    )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    events: queue.Queue = queue.Queue()

    def on_log(log_message: str) -> None:
        events.put({"type": "log", "message": log_message})

    def worker() -> None:
        try:
            result = run_agent(request.message, log_callback=on_log)
            events.put({"type": "final", "result": result})
        except Exception as e:
            events.put({"type": "error", "message": str(e)})
        finally:
            events.put({"type": "done"})

    threading.Thread(target=worker, daemon=True).start()

    def event_stream():
        while True:
            event = events.get()
            yield f"data: {json.dumps(event)}\n\n"
            if event.get("type") == "done":
                break

    return StreamingResponse(event_stream(), media_type="text/event-stream")
