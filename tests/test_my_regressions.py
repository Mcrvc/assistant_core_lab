"""Lab 8 Part E — regression tests for OUR Week-7 failures.

Each test guards a bug users actually hit. It must FAIL on the old code
(check by temporarily undoing the fix) and PASS after the mitigation.
"""
from assistant_core.models import Message


def test_greeting_still_answered(service):
    """Control case: a normal question must never start being refused."""
    r = service.handle(Message(text="hi"))
    assert "Hello" in r.answer


def test_fee_retake_written_as_word_is_counted(service):
    """BUG-7: 'two retakes' was invisible to parse_credits, total too low."""
    r = service.handle(Message(text="tuition for 18 credits and two retakes"))
    assert "8,100,000" not in r.answer


def test_fee_main_credits_written_as_word_is_counted(service):
    """Regression test 3: main credits written as word e.g. 'eighteen credits'."""
    r = service.handle(Message(text="tuition for eighteen credits and two retakes"))
    assert "9,450,000" in r.answer


def test_fractional_credits_rejected(service):
    """BUG-9 (X07): fractional credits like '18.5 credits' must not be truncated and priced."""
    r = service.handle(Message(text="Can you calculate tuition for 18.5 credits?"))
    assert "VND" not in r.answer
    assert "whole number" in r.answer.lower()
