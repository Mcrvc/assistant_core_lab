# Lab 7 · D.4 — Try every state

Owner: Trương Bảo Anh (member-5). Checked on `main` 67281e5 plus the three fixes in this PR,
with `streamlit==1.39.0` (Lab 7 starter version) and the real API.

## How to run

Automated (starts the API itself, drives `ui/app.py` with Streamlit's AppTest):

```bash
pip install -e ".[ui]"
pytest -q tests/test_ui_states.py
```

In the browser, two terminals from the repo root:

```bash
uvicorn assistant_api.main:create_app --factory   # terminal 1, API on :8000
streamlit run ui/app.py                           # terminal 2, UI on :8501
```

## Results

| # | Try | Expected on screen | Result | Test |
|---|---|---|---|---|
| 1 | click an example in the sidebar | question and answer appear | ✅ | `test_state1_sidebar_example_asks_and_answers` |
| 2 | "Can I register my thesis with 118 credits?" | answer + "Sources: H26#5.3 — …" | ✅ `Sources: H26#5.3 — 5.3 Thesis registration` | `test_state2_thesis_question_shows_sources` |
| 3 | "what is the capital of France" | the escalation note (Training Office) | ✅ blue note "…Training Office, room I.101." | `test_state3_out_of_scope_shows_escalation_note` |
| 4 | press Enter on an empty box | nothing is sent | ✅ the browser blocks an empty box; a blank one ("   ") shows "Please type a question." and is not sent | `test_state4_blank_question_is_not_sent` |
| 5 | click 👍 (and 👎) | "Thanks" toast; the buttons disappear | ✅ after fix 2 below (before: buttons stayed until the next click) | `test_state5_vote_thanks_and_hides_buttons` |
| 6 | stop the API, ask again | "Cannot reach the assistant…" instead of a crash | ✅ red banner on top + "⚠️ Cannot reach the assistant. Is the backend running?" | `test_state6_backend_down_shows_friendly_message` |

`pytest -q` → 97 passed (8 of them in `tests/test_ui_states.py`). With the old `ui/app.py`,
both state-5 tests fail, so the test really checks the "buttons disappear" rule.
Every vote sends exactly one `POST /v1/feedback` (201).

## Problems found while checking (fixed in this PR, one commit each)

1. **The page did not start on `main`.** `ui/app.py` imports `WELCOME`, `EXAMPLES`,
   `validate_input` from `ui/logic.py`, but `main` only had L1/L2 → `ImportError`.
   Fix: those three from the starter on `member-1`, L1/L2 from Duy unchanged.
2. **👍/👎 stayed visible after a vote** until the next interaction, because the buttons
   were drawn before the click was handled. Fix: the vote runs as an `on_click` callback.
3. **7 D5 tests failed on streamlit 1.39**: `AppTest.from_file(Path)` → `TypeError: object
   supporting the buffer API required`. Fix: `AppTest.from_file(str(DEMO))`.

Browser screenshots of the six states can be added to this folder later.
