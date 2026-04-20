"""Main FastAPI application."""

from fastapi import FastAPI
from pydantic import BaseModel

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


@app.get("/")
async def root():
    return {"message": "Welcome to Basic AI Agent", "app_name": settings.app_name}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    answer = run_agent(request.message)
    return ChatResponse(answer=answer)
