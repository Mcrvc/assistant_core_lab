"""D5: text fidelity, bounded animation, and reruns without replaying replies."""

from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("streamlit")

from streamlit.testing.v1 import AppTest  # noqa: E402

from ui.api_client import ChatResult  # noqa: E402
from ui.streaming import answer_chunks  # noqa: E402

DEMO = Path(__file__).resolve().parents[1] / "ui" / "streaming_demo.py"


@pytest.mark.parametrize("answer", ["", "  Hello!\n", "**Thesis**\n\n- 120 credits\n- GPA ≥ 2.0\n", "Tiếng Việt 🎓"])
def test_animation_preserves_exact_answer(answer):
    with patch("ui.streaming.sleep"):
        assert "".join(answer_chunks(answer)) == answer


def test_long_answers_do_not_add_an_unbounded_delay():
    with patch("ui.streaming.sleep") as sleep:
        list(answer_chunks("word " * 1000, word_delay=0.02, max_duration=1.5))
    assert sum(call.args[0] for call in sleep.call_args_list) == pytest.approx(1.5)


def test_new_answer_animates_once_and_reruns_do_not_resend():
    answer = "**A complete answer.**\n\nWith the original formatting."
    with patch("ui.api_client.AssistantClient") as client, patch("ui.streaming.sleep"):
        client.return_value.ask.return_value = ChatResult(ok=True, answer=answer, request_id="r1")
        with patch("streamlit.write_stream", side_effect=lambda chunks: "".join(chunks)) as write_stream:
            app = AppTest.from_file(DEMO, default_timeout=10).run()
            app.chat_input[0].set_value("A question").run()
            assert not app.exception
            assert write_stream.call_count == 1
            assert app.session_state.d5_messages[-1]["content"] == answer
            assert app.session_state.d5_messages[-1]["result"]["request_id"] == "r1"
            app.run()
            assert not app.exception
            assert client.return_value.ask.call_count == 1
            assert write_stream.call_count == 1
            assert answer in [item.value for item in app.markdown]


@pytest.mark.parametrize("kind", ["error", "escalate", "disabled"])
def test_errors_escalation_and_disabled_animation_appear_immediately(kind):
    result = ChatResult(ok=kind != "error", answer="Contact the Training Office.",
                        error="Cannot reach the assistant.", escalate=kind == "escalate")
    with patch("ui.api_client.AssistantClient") as client, patch("streamlit.write_stream") as write_stream:
        client.return_value.ask.return_value = result
        app = AppTest.from_file(DEMO, default_timeout=10).run()
        if kind == "disabled":
            app.toggle[0].set_value(False).run()
        app.chat_input[0].set_value("A question").run()
        assert not app.exception
        assert not write_stream.called
        if kind == "error":
            assert app.error[0].value == result.error
        else:
            assert result.answer in [item.value for item in app.markdown]


def test_empty_and_too_long_questions_do_not_call_api():
    with patch("ui.api_client.AssistantClient") as client:
        app = AppTest.from_file(DEMO, default_timeout=10).run()
        app.chat_input[0].set_value("   ").run()
        assert app.warning[0].value == "Please type a question."
        app.chat_input[0].set_value("x" * 2001).run()
        assert "too long" in app.warning[0].value
        assert not client.return_value.ask.called


def test_streamlit_renders_the_final_answer():
    answer = "**Thesis registration**\n\nAt least 120 credits and GPA 2.0."
    with patch("ui.api_client.AssistantClient") as client, patch("ui.streaming.sleep"):
        client.return_value.ask.return_value = ChatResult(ok=True, answer=answer)
        app = AppTest.from_file(DEMO, default_timeout=10).run()
        app.chat_input[0].set_value("Can I register my thesis?").run()
        assert not app.exception
        assert answer in [item.value for item in app.markdown]


def test_demo_displays_a_response_from_the_root_api():
    import httpx
    from fastapi.testclient import TestClient

    from assistant_api.main import create_app
    from ui.api_client import AssistantClient

    with TestClient(create_app()) as backend:
        transport = httpx.MockTransport(
            lambda request: backend.request(request.method, request.url.path, content=request.content)
        )
        client = AssistantClient("http://api.test", transport=transport)
        with patch("ui.api_client.AssistantClient", return_value=client), patch("ui.streaming.sleep"):
            app = AppTest.from_file(DEMO, default_timeout=10).run()
            app.chat_input[0].set_value("Tuition for 18 credits and 2 retake").run()
            assert not app.exception
            assert "9,450,000" in app.session_state.d5_messages[-1]["content"]
            assert app.session_state.d5_messages[-1]["result"]["request_id"]
