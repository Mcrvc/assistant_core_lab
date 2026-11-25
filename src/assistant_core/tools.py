import re

from assistant_core.errors import InvalidRequest

WORD_TO_DIGIT = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14", "fifteen": "15",
    "sixteen": "16", "seventeen": "17", "eighteen": "18", "nineteen": "19", "twenty": "20",
    "twenty-one": "21", "twenty-two": "22", "twenty-three": "23", "twenty-four": "24", "twenty-five": "25",
    "twenty-six": "26", "twenty-seven": "27", "twenty-eight": "28", "twenty-nine": "29", "thirty": "30",
}


def _normalize_number_words(text: str) -> str:
    """Normalize English number words ('one'..'thirty') to digits (BUG-7 mitigation)."""
    norm = text.lower()
    for word, digit in WORD_TO_DIGIT.items():
        norm = re.sub(rf"\b{word}\b", digit, norm)
    return norm


def parse_credits(text: str) -> tuple[int, int]:
    """Extract (credits, retake_credits) from 'fee for 18 credits and 2 retake'."""
    normalized = _normalize_number_words(text)
    if re.search(r"\d+[.,]\d+", normalized):
        raise InvalidRequest("Credits must be a whole number (for example, 18 credits).")
    retake = re.search(r"(\d+)\s*retake", normalized)
    numbers = [int(n) for n in re.findall(r"\d+", normalized)]
    retake_n = int(retake.group(1)) if retake else 0
    others = numbers.copy()
    if retake:
        others.remove(retake_n)
    if not others:
        raise InvalidRequest("How many credits?")
    return others[0], retake_n


def tuition(credits: int, retake: int, rate: int, retake_multiplier: float, max_credits: int) -> int:
    if not 1 <= credits <= max_credits:
        raise InvalidRequest(f"Credits must be between 1 and {max_credits}.")
    return int(credits * rate + retake * rate * retake_multiplier)


import json  # noqa: E402

from pydantic import BaseModel, Field, ValidationError  # noqa: E402


class FeeArgs(BaseModel):
    credits: int = Field(ge=1, le=30)
    retake: int = Field(default=0, ge=0, le=30)


TOOL_SPECS = {
    "calc_fee": {
        "description": "Compute tuition in VND for a number of credits and retake credits.",
        "parameters": FeeArgs.model_json_schema(),
    },
}


def run_tool_call(raw: str, rate: int, retake_multiplier: float, max_credits: int) -> str | None:
    """Return the tool result as text, or None if `raw` is not a tool call. Raises InvalidRequest on bad args."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or "tool" not in data:
        return None
    if data["tool"] != "calc_fee":
        raise InvalidRequest(f"unknown tool {data['tool']!r}")
    try:
        args = FeeArgs.model_validate(data.get("args", {}))
    except ValidationError as exc:
        raise InvalidRequest("invalid tool arguments") from exc
    total = tuition(args.credits, args.retake, rate, retake_multiplier, max_credits)
    return f"Your tuition is {total:,} VND."

