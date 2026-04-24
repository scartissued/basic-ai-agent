"""Agent orchestration logic."""

import json
import logging
import time
from collections.abc import Callable

from openai import APIStatusError, OpenAI, RateLimitError

from app.config import settings
from prompt.prompt import system_prompt
from schema.weather import (
    OutfitRecommendationData,
    RiskAlertData,
    TemperatureData,
    ToolExecutionResponse,
)
from tools.chains import outfit_recommendation_chain, weather_risk_alert_chain
from tools.tools import get_current_weather

logger = logging.getLogger("app.llm")

TOOL_MAP = {
    "get_current_weather": get_current_weather,
    "weather_risk_alert_chain": weather_risk_alert_chain,
    "outfit_recommendation_chain": outfit_recommendation_chain,
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


def _emit_log(message: str, log_callback: Callable[[str], None] | None) -> None:
    _llm_log(message)
    if log_callback:
        log_callback(message)


def _generate_with_retry(client, contents, config, log_callback=None):
    for attempt in range(MAX_RETRIES):
        try:
            _emit_log(
                "Calling LLM",
                log_callback,
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


def _execute_tool(tool_name: str, tool_args: dict) -> ToolExecutionResponse:
    func = TOOL_MAP.get(tool_name)
    if not func:
        return ToolExecutionResponse(success=False, error=f"Unknown tool: {tool_name}")

    try:
        result = func(**tool_args)
        if tool_name == "get_current_weather":
            data = TemperatureData(**result).model_dump()
        elif tool_name == "weather_risk_alert_chain":
            data = RiskAlertData(**result).model_dump()
        elif tool_name == "outfit_recommendation_chain":
            data = OutfitRecommendationData(**result).model_dump()
        else:
            data = result
        return ToolExecutionResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Tool execution failed")
        return ToolExecutionResponse(success=False, error=str(e))


def run_agent(query: str, log_callback: Callable[[str], None] | None = None) -> dict:
    client = _init_client()
    _emit_log(
        f"Starting agent run (query={_truncate_for_log(query, 300)})", log_callback
    )
    used_tools: list[str] = []
    weather_location: str | None = None

    contents = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]

    config = {
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }

    for iteration in range(MAX_ITERATIONS):
        response = _generate_with_retry(client, contents, config, log_callback)
        text = response.choices[0].message.content or ""
        _emit_log(
            f"LLM raw response: {_truncate_for_log(text)}",
            log_callback,
        )
        parsed = _parse_response(text)
        _emit_log(
            f"LLM parsed response keys: {list(parsed.keys())}",
            log_callback,
        )

        contents.append({"role": "assistant", "content": text})

        if "answer" in parsed:
            _emit_log(
                "Agent resolved with answer",
                log_callback,
            )
            return {
                "answer": parsed["answer"],
                "used_tools": used_tools,
                "weather_location": weather_location,
            }

        if "tool" in parsed:
            tool_name = parsed["tool"]
            tool_args = parsed.get("args", {})
            _emit_log(
                "Executing tool "
                f"(tool={tool_name}, "
                f"args={_truncate_for_log(json.dumps(tool_args), 300)})",
                log_callback,
            )
            tool_result = _execute_tool(tool_name, tool_args)
            _emit_log(
                f"Tool result (tool={tool_name}, success={tool_result.success})",
                log_callback,
            )
            used_tools.append(tool_name)
            if (
                tool_name == "get_current_weather"
                and tool_result.success
                and tool_result.data is not None
            ):
                weather_location = tool_result.data.get("location")

            tool_feedback = (
                f"Tool result for {tool_name}:\n{tool_result.model_dump_json()}"
            )
            contents.append({"role": "user", "content": tool_feedback})
        else:
            _emit_log(
                "LLM returned non-tool/non-answer payload; returning raw text",
                log_callback,
            )
            return {
                "answer": text,
                "used_tools": used_tools,
                "weather_location": weather_location,
            }

    _emit_log("Agent stopped after max iterations without final answer", log_callback)
    return {
        "answer": "Sorry, I could not resolve your request after multiple attempts.",
        "used_tools": used_tools,
        "weather_location": weather_location,
    }
