"""Streamlit UI for the travel planning assistant."""

import httpx
import streamlit as st

BACKEND_URL = "http://localhost:8000/chat"

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

typed_prompt = st.chat_input("Ask about weather, risk alerts, or outfit advice...")
prompt = st.session_state.pending_prompt or typed_prompt
st.session_state.pending_prompt = None

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = ask_backend(prompt)
        st.markdown(result["answer"])
    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})

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
