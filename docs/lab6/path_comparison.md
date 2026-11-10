# Lab 6 — Part F: Compare the three assistant paths

Author: Trần Bảo Anh

Branch: `member-4`

Run date: 2026-11-10 (Asia/Saigon)

## Code and evaluation setup

This comparison runs the application in the repository's root `src/assistant_core/`,
using the original 20 questions E01–E20 copied unchanged from
`lab-material/lab06/starter/eval/cases.jsonl` plus the five H1 questions E21–E25
already merged into `eval/cases.jsonl`. There are 18 answerable cases and seven
expected refusals.

The working branch combines these existing contributions:

| Part | Source version | Used for |
|---|---|---|
| C | `main` at `012f916` | The 14 KB chunks, chunker, indexes and retrieval settings |
| D | merged into `main` at `cb26a56` | LLM adapter, prompt, stub and A2 grounding check |
| E | merged into `main` at `fa6166f` | RAG answerer and A1 refusal before generation |
| H1 | `main` at `d9b8cb1` | Five additional evaluation questions E21–E25 |

Part F adapts the supplied comparison script to the root application and injects
each answerer into the same `AssistantService`. The response metadata and optional
RAG service argument are the small shared connections needed by the evaluation.
`guard.py` is copied unchanged from the supplied Lab 6 starter.
The D/E implementations and the existing router are used as provided.

All paths share the router, fee calculator, office directory and privacy guard.
The deterministic baseline disables document retrieval; retrieval quotes the best
chunk; the LLM baseline uses the offline `StubLLM` after the same retrieval step.
The index is BM25, the minimum score is 2.0 and the retrieval limit is three chunks.

## Reproduce the run

Run these commands in PowerShell from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e . pytest
$env:ASSISTANT_DATA_DIR = 'data'
$env:KB_DIR = 'data/kb'
$env:LLM_PROVIDER = 'stub'
$env:RETRIEVAL_KIND = 'bm25'
$env:RETRIEVAL_MIN_SCORE = '2.0'
.\.venv\Scripts\python.exe eval/compare_paths.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_eval_paths.py
```

The recorded run used Windows, Python 3.14.7, Pydantic 2.14.3, httpx 0.27.2,
python-dotenv 1.2.4 and pytest 9.2.0, resolved from `pyproject.toml`.
The repository's separately pinned `requirements.txt` targets Python 3.12.
The comparison always uses the stub and makes no external model calls.

## Measured results

| Path | Correct /25 | Abstain correct /7 | p50 ms | Max ms | Controllability (1–5) | Main failure mode |
|---|---:|---:|---:|---:|---:|---|
| deterministic | 9/25 | 7/7 | 0.0 | 1.3 | 5 | Cannot answer document questions; router can send policy questions to tools or offices. |
| retrieval | 20/25 | 6/7 | 0.0 | 0.2 | 4 | Router mistakes and keyword ranking can select an irrelevant paragraph. |
| llm (provider: stub) | 20/25 | 6/7 | 0.2 | 1.0 | 4 | The stub repeats the top source and cannot decide whether it actually answers the question. |

Controllability scores are qualitative judgments, not measurements. The stub is
deterministic, and its output is checked against a schema and allowed source IDs;
this run does not measure a real model's behavior.

Raw output from the recorded run:

```text
path                correct  abstain ok  p50 ms  max ms
deterministic          9/25       7/7     0.0     1.3   fails: E01 E02 E05 E06 E07 E08 E09 E10 E11 E12 E13 E14 E15 E21 E24 E25
retrieval             20/25       6/7     0.0     0.2   fails: E13 E14 E15 E19 E25
llm (stub)            20/25       6/7     0.2     1.0   fails: E13 E14 E15 E19 E25
```

`correct` uses the supplied rubric: an expected source ID must appear in the
response, an expected text fragment must appear in the answer, or an expected
refusal must have `path="abstain"` or `intent="unknown"`. It does not verify every
claim in an answer. `abstain ok` counts only the seven expected refusals.
Latency measures one `service.handle()` call per case, including routing and
validation but excluding service construction and index building. Values are
rounded to one decimal place, so 0.0 ms does not mean zero processing time.
These are observations from one local run; timings vary between runs.

## Observed failures

| Case | Expected behavior | Observed behavior and cause |
|---|---|---|
| E13: “when is tuition due” | Cite `F26#3`, the payment deadline. | Every path returns “How many credits?” because the router sees “tuition” and calls the fee calculator before retrieval. A separate search also ranks `F26#1` (2.277) above `F26#3` (1.484). |
| E14: “can I take 32 credits” | Cite `H26#6.1`, the credit-load policy. | Retrieval and the stub cite `H26#7.2`, exam absence (2.086), above the credit-load chunk (1.475). Keyword ranking favors the exam paragraph, which contains “take”; it does not understand the intended credit-load question. The deterministic path refuses. |
| E15: “how long can I keep a library book” | Cite `S26#1`, the borrowing policy. | Every path gives the library room and opening hours because the router treats the word “library” as an office lookup. Searching directly finds `S26#1` with score 2.299, but the question never reaches retrieval. |
| E19: “is the final exam open-book” | Refuse because the KB does not specify the exam format. | Retrieval and the stub cite exam absence, `H26#7.2` (5.620). This passes the relevance threshold and the allowed-source check, but the paragraph does not answer the question. The deterministic path correctly refuses. |
| E25: “what is the tuition rate per credit” | Cite `F26#1`, the tuition-rate policy. | Every path routes the question to the fee calculator because it contains “tuition”; without a credit count, the tool asks “How many credits?” instead of returning a source. |

These failures are recorded for Part F; they have not been fixed as part of this task.

## Recommendation — three sentences

I would use the retrieval path for handbook questions because it quotes the official document and shows its source.
It achieves the same 20/25 score as the stub LLM on these cases while avoiding the extra generation step, although its routing and relevance mistakes still need attention.
I would fix E19 first because presenting a related paragraph as an answer is misleading, and the assistant should refuse when the source does not establish the requested fact.

## Validation

- Part F tests: **12 passed**.
- Part F checks cover source/text/refusal scoring, separate refusal counts,
  failure IDs, selection of the three paths and preservation of exact fee calculation.
- Ruff checks passed for the new evaluation/tests, supplied guard and modified service.
- `pip check` found no broken requirements.
- E01–E20 are byte-for-byte identical to the supplied starter dataset, and the five H1 cases from `main` are preserved as E21–E25.

The full repository suite cannot currently collect `tests/test_rag.py` because
`run_tool_call` is absent from `assistant_core.tools` on the `main` base. This is
an existing integration issue outside Part F; the Part F comparison and its tests run successfully.
