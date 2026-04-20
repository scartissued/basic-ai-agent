"""Streamlit UI for the Basic AI Agent."""

import httpx
import streamlit as st

BACKEND_URL = "http://localhost:8000/chat"

st.set_page_config(page_title="Basic AI Agent", page_icon="🌤️")
st.title("🌤️ Weather AI Agent")
st.markdown("Ask me about the weather in any city!")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about the weather..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = httpx.post(
                    BACKEND_URL,
                    json={"message": prompt},
                    timeout=30.0,
                )
                response.raise_for_status()
                answer = response.json()["answer"]
            except httpx.ConnectError:
                answer = (
                    "⚠️ Could not connect to the backend. "
                    "Make sure FastAPI is running on port 8000."
                )
            except httpx.HTTPStatusError as e:
                answer = f"⚠️ Backend error: {e.response.status_code}"
            except Exception as e:
                answer = f"⚠️ Something went wrong: {e}"

        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
