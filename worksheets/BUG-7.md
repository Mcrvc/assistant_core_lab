# BUG-7: Fee question with the number written as a word gives a wrong total

**Found by:** Lab 8 Part C.3   **Date:** 2026-11-23   **Severity:** major
**Where:** AI / backend (`src/assistant_core/tools.py`)

## Steps to reproduce
1. Call `parse_credits("tuition for 18 credits and two retakes")` (or `POST /v1/chat {"message": "tuition for 18 credits and two retakes"}`).

## Expected
`(18, 2)` (total `9,450,000 VND`)

## Actual (paste the exact output or error)
`(18, 0)` (total `8,100,000 VND` — `"two"` is ignored because `parse_credits` only matches `\d+`).

## Evidence
- Python shell: `from assistant_core.tools import parse_credits; parse_credits("tuition for 18 credits and two retakes")` → `(18, 0)`

## Cause (after investigation)
`parse_credits` in `src/assistant_core/tools.py` uses `re.search(r"(\d+)\s*retake", text)` and `re.findall(r"\d+", text)`, so number words like `"two"` are not recognized.

## Fix (commit / PR link) and regression test name
TBD (Part E — decide whether to support `"one"`–`"ten"` or prompt the user to enter digits, then add `test_retake_number_as_word` in `tests/test_my_regressions.py`).
