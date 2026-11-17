"""Lab 7 D.4 — "Try every state", automated.

Each test drives the real page (ui/app.py) with Streamlit's AppTest against the
real API (assistant_api.main:create_app) started in a background thread, so
the whole chain UI -> HTTP -> API -> assistant_core runs, like in the browser.
Feedback is kept in the API's memory, so nothing is written to the repo.
"""
from __future__ import annotations

import socket
import threading
import time
from pathlib import Path

import pytest

st_testing = pytest.importorskip("streamlit.testing.v1")
uvicorn = pytest.importorskip("uvicorn")

from assistant_api.main import create_app  # noqa: E402
from assistant_core.config import load_settings  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
APP = str(ROOT / "ui" / "app.py")  # str: AppTest on streamlit 1.39 does not accept Path


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def api_url():
    settings = load_settings(env_file=None).model_copy(update={
        "data_dir": ROOT / "data", "kb_dir": ROOT / "data" / "kb", "rate_limit_per_min": 1000,
    })
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(create_app(settings), host="127.0.0.1", port=port,
                                           log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 15
    while not server.started:
        if time.monotonic() > deadline:
            pytest.fail("API did not start")
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture
def page(api_url, monkeypatch):
    monkeypatch.setenv("ASSISTANT_API_URL", api_url)
    at = st_testing.AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception
    return at


def _messages(at):
    return at.session_state.messages


def _vote_buttons(at):
    return [b for b in at.button if b.label in ("👍", "👎")]


def test_page_loads_with_backend_up(page):
    assert not page.error  # no red "backend is not reachable" banner
    assert _messages(page)[0]["role"] == "assistant"  # welcome message


def test_state1_sidebar_example_asks_and_answers(page):
    example = page.sidebar.button[0]
    example.click().run()
    msgs = _messages(page)
    assert not page.exception
    assert msgs[-2] == {"role": "user", "content": example.label}
    assert msgs[-1]["role"] == "assistant" and msgs[-1]["content"]


def test_state2_thesis_question_shows_sources(page):
    page.chat_input[0].set_value("Can I register my thesis with 118 credits?").run()
    captions = [c.value for c in page.caption]
    assert any(c.startswith("Sources: H26#5.3 — ") for c in captions), captions


def test_state3_out_of_scope_shows_escalation_note(page):
    page.chat_input[0].set_value("what is the capital of France").run()
    notes = [i.value for i in page.info]
    assert any("Training Office, room I.101" in n for n in notes), notes


def test_state4_blank_question_is_not_sent(page):
    before = len(_messages(page))
    page.chat_input[0].set_value("   ").run()
    assert len(_messages(page)) == before
    assert [w.value for w in page.warning] == ["Please type a question."]


@pytest.mark.parametrize("label,thanks", [("👍", "Thanks for your feedback!"),
                                          ("👎", "Thanks — we will look at this answer.")])
def test_state5_vote_thanks_and_hides_buttons(page, label, thanks):
    page.chat_input[0].set_value("I lost my student card").run()
    assert _vote_buttons(page), "an answer must offer 👍/👎"
    next(b for b in page.button if b.label == label).click().run()
    assert thanks in [t.value for t in page.toast]
    assert not _vote_buttons(page), "buttons must disappear right after one vote"


def test_state6_backend_down_shows_friendly_message(monkeypatch):
    monkeypatch.setenv("ASSISTANT_API_URL", f"http://127.0.0.1:{_free_port()}")  # nothing listens
    at = st_testing.AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert "not reachable" in at.error[0].value  # red banner at the top
    at.chat_input[0].set_value("I lost my student card").run()
    assert not at.exception  # no crash
    assert "Cannot reach the assistant" in _messages(at)[-1]["content"]
