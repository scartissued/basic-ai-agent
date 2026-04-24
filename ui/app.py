"""Streamlit UI for the travel planning assistant."""

import json
import time

import httpx
import streamlit as st

BACKEND_URL = "http://localhost:8000/chat"
BACKEND_STREAM_URL = "http://localhost:8000/chat/stream"

st.set_page_config(page_title="Travel Planner Assistant", page_icon=":luggage:")
st.title("Travel Planner Assistant")
st.markdown("Use weather-aware prompts for travel, risk checks, and outfit ideas.")
st.markdown(
    """
    <style>
    .stMainBlockContainer {
        padding-bottom: 10rem;
    }
    div[data-testid="stVerticalBlock"] > div:has(> div [data-testid="stPills"]) {
        position: fixed;
        left: 1rem;
        right: 1rem;
        bottom: 4.25rem;
        z-index: 1000;
        background: rgba(15, 17, 22, 0.92);
        border: 1px solid rgba(250, 250, 250, 0.08);
        border-radius: 0.75rem;
        padding: 0.35rem 0.6rem 0.5rem 0.6rem;
        backdrop-filter: blur(6px);
    }
    div[data-testid="stVerticalBlock"] > div:has(> div [data-testid="stPills"]) p {
        font-size: 0.8rem;
        margin-bottom: 0.2rem;
    }
    .llm-log-block {
        padding: 0.35rem 0.1rem 0.2rem 0.1rem;
        color: rgba(230, 230, 230, 0.86);
        font-size: 0.75rem;
        line-height: 1.35;
        white-space: pre-wrap;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .stExpander {
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 0.55rem !important;
        background: rgba(140, 140, 140, 0.14) !important;
    }
    .stExpander > details {
        background: transparent !important;
    }
    .stExpander > details > summary {
        background: rgba(160, 160, 160, 0.16) !important;
        border-radius: 0.5rem 0.5rem 0 0 !important;
    }
    .stExpander > details > div[role="region"] {
        background: rgba(130, 130, 130, 0.13) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def ask_backend(prompt: str) -> dict:
    try:
        response = httpx.post(
            BACKEND_URL,
            json={"message": prompt},
            timeout=30.0,
        )
        response.raise_for_status()
        body = response.json()
        return {
            "answer": body.get("answer", ""),
            "used_tools": body.get("used_tools", []),
            "weather_location": body.get("weather_location"),
        }
    except httpx.ConnectError:
        return {
            "answer": (
                "Could not connect to the backend. "
                "Make sure FastAPI is running on port 8000."
            ),
            "used_tools": [],
            "weather_location": None,
        }
    except httpx.HTTPStatusError as e:
        return {
            "answer": f"Backend error: {e.response.status_code}",
            "used_tools": [],
            "weather_location": None,
        }
    except Exception as e:
        return {
            "answer": f"Something went wrong: {e}",
            "used_tools": [],
            "weather_location": None,
        }


def ask_backend_stream(prompt: str, log_placeholder) -> dict:
    log_lines: list[str] = []
    try:
        with httpx.stream(
            "POST",
            BACKEND_STREAM_URL,
            json={"message": prompt},
            timeout=120.0,
        ) as response:
            response.raise_for_status()
            for raw_line in response.iter_lines():
                if not raw_line or not raw_line.startswith("data: "):
                    continue
                payload = json.loads(raw_line[len("data: ") :])
                event_type = payload.get("type")

                if event_type == "log":
                    line = payload.get("message", "")
                    if line:
                        log_lines.append(line)
                        log_placeholder.caption("Live LLM logs")
                        log_placeholder.code("\n".join(log_lines[-12:]))
                elif event_type == "final":
                    result = payload.get("result", {})
                    return {
                        "answer": result.get("answer", ""),
                        "used_tools": result.get("used_tools", []),
                        "weather_location": result.get("weather_location"),
                        "logs": log_lines,
                    }
                elif event_type == "error":
                    return {
                        "answer": f"Backend stream error: {payload.get('message', 'unknown error')}",
                        "used_tools": [],
                        "weather_location": None,
                        "logs": log_lines,
                    }
    except Exception:
        # Fallback to non-stream call if stream is unavailable.
        return ask_backend(prompt)

    return {
        "answer": "No final response received from stream.",
        "used_tools": [],
        "weather_location": None,
        "logs": log_lines,
    }


if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
if "last_city" not in st.session_state:
    st.session_state.last_city = ""
if "show_quick_actions" not in st.session_state:
    st.session_state.show_quick_actions = False

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        logs = message.get("logs", [])
        if logs:
            duration_s = message.get("duration_s", 0.0)
            with st.expander(f"Worked for {duration_s:.1f} seconds", expanded=False):
                st.markdown(
                    f'<div class="llm-log-block">{"<br/>".join(logs)}</div>',
                    unsafe_allow_html=True,
                )

typed_prompt = st.chat_input("Ask about weather, risk alerts, or outfit advice...")
prompt = st.session_state.pending_prompt or typed_prompt
st.session_state.pending_prompt = None

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        log_placeholder = st.empty()
        started_at = time.perf_counter()
        result = ask_backend_stream(prompt, log_placeholder)
        duration_s = time.perf_counter() - started_at
        logs = result.get("logs", [])
        if logs:
            with log_placeholder.container():
                with st.expander(f"Worked for {duration_s:.1f} seconds", expanded=False):
                    st.markdown(
                        f'<div class="llm-log-block">{"<br/>".join(logs)}</div>',
                        unsafe_allow_html=True,
                    )
        else:
            log_placeholder.empty()
        st.markdown(result["answer"])
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "logs": logs,
            "duration_s": duration_s,
        }
    )

    used_tools = result.get("used_tools", [])
    st.session_state.show_quick_actions = "get_current_weather" in used_tools
    if st.session_state.show_quick_actions:
        location = (result.get("weather_location") or "").strip()
        if location:
            st.session_state.last_city = location

city = st.session_state.last_city
if city and st.session_state.show_quick_actions:
    st.caption(f"Quick actions for {city}")
    options = [
        f"Current weather in {city}",
        f"Risk alerts for {city}",
        f"Outfit advice for {city}",
    ]
    selected = st.pills(
        "Suggestions",
        options=options,
        selection_mode="single",
        label_visibility="collapsed",
        key=f"quick_actions_{city}_{len(st.session_state.messages)}",
    )
    if selected:
        if selected.startswith("Current weather"):
            st.session_state.pending_prompt = f"What is the current weather in {city}?"
        elif selected.startswith("Risk alerts"):
            st.session_state.pending_prompt = (
                f"Any weather risk alerts for {city} right now?"
            )
        elif selected.startswith("Outfit advice"):
            st.session_state.pending_prompt = (
                f"What should I wear in {city} for a walking trip?"
            )
        st.rerun()
