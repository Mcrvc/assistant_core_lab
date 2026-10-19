from assistant_core.models import Intent

GREETINGS = frozenset({"hi", "hello", "hey", "xin chao"})


def route(text: str, office_names: set[str]) -> Intent:
    """Classify a user message into an intent."""
    t = text.lower().strip().rstrip("?!.")

    if t in GREETINGS:
        return Intent.GREETING

    if "fee" in t or "tuition" in t:
        return Intent.FEE

    if any(name.lower() in t for name in office_names):
        return Intent.OFFICE

    return Intent.RULE
