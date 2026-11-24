"""Deterministic guardrails that run BEFORE retrieval or any LLM call."""

from __future__ import annotations

import re

PRIVATE_PATTERNS = [
    r"\b(my|a) (friend|classmate|roommate)'?s?\b.*\b(grade|score|gpa|result|phone|address)",
    r"\b(grade|score|gpa|result|phone|address)s?\b.*\b(of|for) (another|other) student",
    r"\b(grade|score|gpa|result|phone|address)s?\b.*\b(my|a) (friend|classmate|roommate)",
    r"\b\d{8}\b",  # looks like a student id
]


def is_private_request(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in PRIVATE_PATTERNS)


PRIVATE_REPLY = "I can't share information about other students. You can only see your own records after logging in."


INJECTION_PATTERNS = [
    r"\bignore (all |any |the )?(previous|above|prior|earlier) (instructions|rules|messages)",
    r"\b(reveal|show|print|repeat) (me )?(your|the) (system )?(prompt|instructions|rules)",
    r"\byou are now\b",
    r"\b(developer|debug|admin|god) mode\b",
    r"\bpretend (to be|you are)\b",
]


def is_injection(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in INJECTION_PATTERNS)


INJECTION_REPLY = "I'm here to help with university questions only. I can't follow instructions that try to change my behaviour."
