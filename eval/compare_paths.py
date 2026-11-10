#!/usr/bin/env python3
"""Compare deterministic, retrieval and stub-LLM paths on the Lab 6 cases.

Run from the repository root: python eval/compare_paths.py
The three paths share the root application's router, tools and privacy guard.
The LLM baseline always uses the offline StubLLM; no API key is needed.
Adapted from lab-material/lab06/starter/eval/compare_paths.py.
"""

from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from assistant_core.config import Settings, load_settings
from assistant_core.knowledge import Handbook, OfficeDirectory
from assistant_core.llm import StubLLM
from assistant_core.models import Message, Response
from assistant_core.rag.answerer import RagAnswerer
from assistant_core.rag.chunker import load_folder
from assistant_core.rag.index import make_index
from assistant_core.responder import TemplateResponder
from assistant_core.service import AssistantService

CASES_PATH = Path(__file__).with_name("cases.jsonl")


class NoAnswer:
    """Disable document answers for the deterministic baseline."""

    def search(self, query: str, k: int = 3) -> list:
        return []


def correct(case: dict, response: Response) -> bool:
    """Use the course rubric: refusal, expected text, or expected source ID."""
    if case.get("expect_abstain"):
        return response.path == "abstain" or response.intent.value == "unknown"
    if "expect_contains" in case:
        return case["expect_contains"] in response.answer
    return any(source.id == case["expect_source"] for source in response.sources)


def build_paths(settings: Settings) -> dict[str, AssistantService]:
    offices = OfficeDirectory.from_csv(settings.data_dir / "offices.csv")
    handbook = Handbook.from_json(settings.data_dir / "handbook.json")
    chunks = load_folder(settings.kb_dir)
    if not chunks:
        raise ValueError(f"No knowledge-base chunks found in {settings.kb_dir}")
    index = make_index(settings.retrieval_kind, chunks)
    paths = {
        "deterministic": RagAnswerer(NoAnswer(), None, settings.retrieval_min_score),
        "retrieval": RagAnswerer(index, None, settings.retrieval_min_score),
        "llm (stub)": RagAnswerer(index, StubLLM(), settings.retrieval_min_score),
    }
    return {
        name: AssistantService(settings, offices, handbook, TemplateResponder(), rag)
        for name, rag in paths.items()
    }


def evaluate(service: AssistantService, cases: list[dict]) -> dict:
    ok = abstain_ok = abstain_total = 0
    latencies, failures = [], []
    for case in cases:
        start = time.perf_counter()
        response = service.handle(Message(text=case["question"]))
        latencies.append((time.perf_counter() - start) * 1000)
        good = correct(case, response)
        ok += good
        if case.get("expect_abstain"):
            abstain_total += 1
            abstain_ok += good
        if not good:
            failures.append(case["id"])
    return {
        "correct": ok,
        "total": len(cases),
        "abstain_ok": abstain_ok,
        "abstain_total": abstain_total,
        "p50_ms": statistics.median(latencies),
        "max_ms": max(latencies),
        "failures": failures,
    }


def main() -> int:
    settings = load_settings()
    cases = [json.loads(line) for line in CASES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"{'path':18} {'correct':>8} {'abstain ok':>11} {'p50 ms':>7} {'max ms':>7}")
    for name, service in build_paths(settings).items():
        result = evaluate(service, cases)
        print(
            f"{name:18} {result['correct']:>5}/{result['total']}"
            f" {result['abstain_ok']:>7}/{result['abstain_total']}"
            f" {result['p50_ms']:7.1f} {result['max_ms']:7.1f}"
            f"   fails: {' '.join(result['failures'])}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
