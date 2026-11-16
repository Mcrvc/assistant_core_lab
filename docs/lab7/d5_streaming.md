# Lab 7 — D5 and the typing animation bonus

Author: Trần Bảo Anh (`member-4`)

## D5: the concept

Streaming means displaying pieces of an answer as they arrive, while a model is
still producing the rest. This reduces the perceived waiting time for long answers.
The current `POST /v1/chat` endpoint returns one complete JSON response, so the UI
shows “Thinking…” while waiting for that response.

The bonus implemented here is the typing animation allowed by the assignment:
after the API has returned the completed answer, Streamlit displays it word by
word using `st.write_stream`. This does not change model generation or network
latency and does not claim to stream tokens from the backend.

## Files

- `ui/streaming.py`: reusable `answer_chunks` and `display_answer` helpers.
- `ui/streaming_demo.py`: working D5 demonstration connected to the HTTP API.
- `ui/api_client.py`: the client supplied in the Lab 7 starter, copied unchanged.
- `tests/test_ui_streaming.py`: text fidelity, limited animation wait, and page tests.

`main` at `db36290` contains the Lab 7 materials but no root chat page yet. The
standalone demonstration lets D5 be reviewed before the other UI contributions
are merged. It does not replace their shared chat page or complete L1/L2/F1.
The full API result, including sources, request ID and flags, is retained in the
demo's session history for later integration.

## Run from the repository root

Install the UI extra into the existing project environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[ui]"
```

Terminal 1 — backend:

```powershell
$env:LLM_PROVIDER = 'stub'
.\.venv\Scripts\python.exe -m uvicorn assistant_api.main:create_app --factory
```

Terminal 2 — demonstration:

```powershell
.\.venv\Scripts\python.exe -m streamlit run ui/streaming_demo.py
```

Open `http://localhost:8501`. If needed, set `ASSISTANT_API_URL` before starting
the UI. Ask “Can I register my thesis with 118 credits?” or
“Tuition for 18 credits and 2 retake”. The UI talks to the backend through HTTP.

## What to observe

1. Submit a question: the spinner appears while waiting for the API, followed by
   the new answer appearing word by word.
2. Switch off **Animate new answers**: the next answer appears immediately.
3. Toggle that control or otherwise rerun: previous answers appear immediately
   without being requested again or replaying their animation.
4. Ask an out-of-scope question: an escalation response appears immediately.
5. Stop the backend and submit another question: a readable error appears without
   animating it or crashing the page.

The generator preserves the exact original text, including whitespace, Markdown,
Unicode and line breaks. Added sleep is capped at 1.5 seconds per answer; Streamlit
rendering and network time are separate. Conversation state is saved before
animation so a rerun retains the completed result.

## Integrate with the team's chat page

Import the helper into the root UI:

```python
from ui.streaming import display_answer
```

Use it only when rendering a newly received successful response:

```python
with st.chat_message("assistant"):
    display_answer(result.answer, animate=not result.escalate)
```

Keep the existing logic for saving history, sources, special status notes and
feedback IDs. History should continue to use `st.markdown`, so later clicks never
replay old animations. Error responses should continue to use `st.error`.
The demonstration includes an optional toggle; the shared page may reuse it.

## Check

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_ui_streaming.py
.\.venv\Scripts\python.exe -m pytest -q tests
```

Install the UI extra before testing this feature. Its test module is skipped in
backend-only environments where Streamlit is not installed.

Validated on 2026-11-16 with Python 3.14.7 and Streamlit 1.67.0:

- D5 tests: **12 passed**, including a response from the root API rendered by AppTest.
- Full root suite: **89 passed**.
- Ruff checks for the D5 implementation and tests: passed.
- `pip check`: no broken requirements.

The UI extra permits Streamlit 1.39 or newer within version 1. The local Python
3.14 environment uses a newer compatible release; the supplied course materials
and their dependency pins are unchanged.
