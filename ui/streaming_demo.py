"""Run from the repo root: streamlit run ui/streaming_demo.py."""

import os
import sys
import uuid
from dataclasses import asdict
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ui.api_client import AssistantClient  # noqa: E402
from ui.streaming import display_answer  # noqa: E402

st.set_page_config(page_title="Assistant — typing preview", page_icon="🎓")
st.title("Assistant — typing preview")
st.caption("D5 bonus: ask a question to see the new answer appear word by word.")
animate = st.toggle("Animate new answers", value=True)

if "d5_session_id" not in st.session_state:
    st.session_state.d5_session_id = uuid.uuid4().hex[:12]
if "d5_messages" not in st.session_state:
    st.session_state.d5_messages = []

for message in st.session_state.d5_messages:
    with st.chat_message(message["role"]):
        if message.get("error"):
            st.error(message["content"])
        else:
            display_answer(message["content"], animate=False)

question = st.chat_input("Ask about fees, offices or the handbook…")
if question:
    question = question.strip()
    if not question:
        st.warning("Please type a question.")
    elif len(question) > 2000:
        st.warning("Your question is too long (max 2000 characters).")
    else:
        st.session_state.d5_messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        client = AssistantClient(os.getenv("ASSISTANT_API_URL", "http://127.0.0.1:8000"))
        with st.spinner("Thinking…"):
            result = client.ask(question, st.session_state.d5_session_id)
        message = {"role": "assistant", "content": result.answer if result.ok else result.error,
                   "error": not result.ok, "result": asdict(result)}
        st.session_state.d5_messages.append(message)
        with st.chat_message("assistant"):
            if result.ok:
                display_answer(result.answer, animate=animate and not result.escalate)
            else:
                st.error(result.error)
