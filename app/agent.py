"""Agent orchestration logic."""

import json
import logging
import time

from google import genai
from google.genai import errors as genai_errors

from app.config import settings
from prompt.prompt import system_prompt
from schema.weather import TemperatureData, WeatherResponse
from tools.tools import get_current_weather

logger = logging.getLogger(__name__)

TOOL_MAP = {
    "get_current_weather": get_current_weather,
}

MAX_ITERATIONS = 5
MAX_RETRIES = 3
RETRY_DELAY = 30


def _generate_with_retry(client, contents, config):
    for attempt in range(MAX_RETRIES):
        try:
            return client.models.generate_content(
                model=settings.gemini_model,
                contents=contents,
                config=config,
            )
        except genai_errors.ClientError as e:
            if e.status == "RESOURCE_EXHAUSTED" and attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY * (attempt + 1)
                logger.warning("Rate limited, retrying in %ds...", wait)
                time.sleep(wait)
            else:
                raise


def _init_client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


def _parse_response(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"answer": text}


def _execute_tool(tool_name: str, tool_args: dict) -> WeatherResponse:
    func = TOOL_MAP.get(tool_name)
    if not func:
        return WeatherResponse(success=False, error=f"Unknown tool: {tool_name}")

    try:
        result = func(**tool_args)
        data = TemperatureData(**result)
        return WeatherResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Tool execution failed")
        return WeatherResponse(success=False, error=str(e))


def run_agent(query: str) -> str:
    client = _init_client()

    contents = [
        genai.types.Content(
            role="user",
            parts=[genai.types.Part.from_text(text=query)],
        ),
    ]

    config = genai.types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.0,
        response_mime_type="application/json",
    )

    for _ in range(MAX_ITERATIONS):
        response = _generate_with_retry(client, contents, config)
        text = response.text
        parsed = _parse_response(text)

        contents.append(
            genai.types.Content(
                role="model",
                parts=[genai.types.Part.from_text(text=text)],
            )
        )

        if "answer" in parsed:
            return parsed["answer"]

        if "tool" in parsed:
            tool_name = parsed["tool"]
            tool_args = parsed.get("args", {})
            tool_result = _execute_tool(tool_name, tool_args)

            tool_feedback = (
                f"Tool result for {tool_name}:\n{tool_result.model_dump_json()}"
            )
            contents.append(
                genai.types.Content(
                    role="user",
                    parts=[genai.types.Part.from_text(text=tool_feedback)],
                )
            )
        else:
            return text

    return "Sorry, I could not resolve your request after multiple attempts."
