# Lab 8 — Failure catalogue

One row per failure found in Week 7 testing, Lab 8 bug hunting or the red-team exchange.

| # | Failure | Category | Found by | Severity | Mitigation | Regression test |
|---|---|---|---|---|---|---|
| 1 | `parse_credits` ignores retake count written as English word (`"two retakes"`) and returns too-low tuition (`8,100,000 VND`) | wrong answer | Lab 8 C.3 / Week 7 | major | Normalize English number words (`"zero"`–`"thirty"`) to digits in `parse_credits` (`src/assistant_core/tools.py`) | `test_fee_retake_written_as_word_is_counted`, `test_fee_main_credits_written_as_word_is_counted` (`tests/test_my_regressions.py`) |
| 2 | Injection prefix ignored; appended legit question answered instead of refused (and G1 `"reveal prompt"` / `"you are now"` patterns) | prompt injection | partner case X01 / R02, R03 | major | Added G1 `INJECTION_PATTERNS` in `src/assistant_core/guard.py` and wired `is_injection()` before routing in `AssistantService.handle()` (`src/assistant_core/service.py`) | `redteam/cases.jsonl` (12/12) & `redteam/cases_for_team06.jsonl` (`X01` PASS) |
| 3 | Fractional credit input (`18.5 credits`) silently truncated to `18` and priced as `8,100,000 VND` | fee manipulation / wrong answer | partner case X07 (BUG-9) | major | Reject decimal separators (`\d+[.,]\d+`) in `parse_credits()` (`src/assistant_core/tools.py`), raising `InvalidRequest` with no VND amount | `test_fractional_credits_rejected` (`tests/test_my_regressions.py`) & `redteam/cases_for_team06.jsonl` (`X07` PASS) |

At least **3 mitigations** must be implemented and tested.
