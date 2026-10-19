import pytest
from pydantic import ValidationError

from assistant_core.models import Intent, Message, Response, Source


def test_message_defaults_to_local_session():
    message = Message(text="hello")

    assert message.session_id == "local"


@pytest.mark.parametrize("text", ["", "x" * 2001])
def test_message_rejects_invalid_length(text):
    with pytest.raises(ValidationError):
        Message(text=text)


def test_response_has_typed_sources_and_safe_defaults():
    first = Response(
        answer="A rule applies.",
        intent=Intent.RULE,
        sources=[Source(id="H26-5.3", title="Thesis registration")],
    )
    second = Response(answer="Hello!", intent=Intent.GREETING)

    assert first.sources[0].id == "H26-5.3"
    assert second.sources == []
    assert second.degraded is False
