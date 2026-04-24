"""Agent orchestration logic."""

import json
import logging
import time

from openai import APIStatusError, OpenAI, RateLimitError

from app.config import settings
from prompt.prompt import system_prompt
from schema.weather import TemperatureData, WeatherResponse
from tools.tools import get_current_weather

logger = logging.getLogger("app.llm")

TOOL_MAP = {
    "get_current_weather": get_current_weather,
}

MAX_ITERATIONS = 5
MAX_RETRIES = 3
RETRY_DELAY = 30
MAX_LOG_CHARS = 1000


def _truncate_for_log(value: str, max_chars: int = MAX_LOG_CHARS) -> str:
    if len(value) <= max_chars:
        return value
    return f"{value[:max_chars]}... [truncated {len(value) - max_chars} chars]"


def _llm_log(message: str) -> None:
    print(f"[LLM] {message}", flush=True)


def _generate_with_retry(client, contents, config):
    for attempt in range(MAX_RETRIES):
        try:
            _llm_log(
                "Calling OpenAI "
                f"model={settings.openai_model} "
                f"(retry_attempt={attempt + 1}/{MAX_RETRIES}, "
                f"message_count={len(contents)})"
            )
            return client.chat.completions.create(
                model=settings.openai_model,
                messages=contents,
                temperature=config["temperature"],
                response_format=config["response_format"],
            )
        except (RateLimitError, APIStatusError) as e:
            status_code = getattr(e, "status_code", None)
            if status_code == 429 and attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY * (attempt + 1)
                logger.warning("Rate limited, retrying in %ds...", wait)
                time.sleep(wait)
            else:
                logger.exception("OpenAI request failed (status_code=%s)", status_code)
                raise


def _init_client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


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
    _llm_log(f"Starting agent run (query={_truncate_for_log(query, 300)})")

    contents = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]

    config = {
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }

    for iteration in range(MAX_ITERATIONS):
        response = _generate_with_retry(client, contents, config)
        text = response.choices[0].message.content or ""
        _llm_log(
            "LLM raw response "
            f"(iteration={iteration + 1}/{MAX_ITERATIONS}): "
            f"{_truncate_for_log(text)}"
        )
        parsed = _parse_response(text)
        _llm_log(
            "LLM parsed response keys "
            f"(iteration={iteration + 1}/{MAX_ITERATIONS}): "
            f"{list(parsed.keys())}"
        )

        contents.append({"role": "assistant", "content": text})

        if "answer" in parsed:
            _llm_log(
                f"Agent resolved with answer (iteration={iteration + 1}/{MAX_ITERATIONS})"
            )
            return parsed["answer"]

        if "tool" in parsed:
            tool_name = parsed["tool"]
            tool_args = parsed.get("args", {})
            _llm_log(
                "Executing tool "
                f"(iteration={iteration + 1}/{MAX_ITERATIONS}, "
                f"tool={tool_name}, "
                f"args={_truncate_for_log(json.dumps(tool_args), 300)})"
            )
            tool_result = _execute_tool(tool_name, tool_args)
            _llm_log(
                f"Tool result (tool={tool_name}, success={tool_result.success})"
            )

            tool_feedback = (
                f"Tool result for {tool_name}:\n{tool_result.model_dump_json()}"
            )
            contents.append({"role": "user", "content": tool_feedback})
        else:
            _llm_log("LLM returned non-tool/non-answer payload; returning raw text")
            return text

    _llm_log("Agent stopped after max iterations without final answer")
    return "Sorry, I could not resolve your request after multiple attempts."
