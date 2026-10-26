from assistant_core.models import Intent
from assistant_core.router import route


def test_route_greeting():
    assert route("hello", set()) == Intent.GREETING


def test_route_fee():
    assert route("tuition for 18 credits", set()) == Intent.FEE


def test_route_office():
    assert route("where is the library?", {"library"}) == Intent.OFFICE


def test_route_rule():
    assert route("can I register my thesis?", set()) == Intent.RULE
