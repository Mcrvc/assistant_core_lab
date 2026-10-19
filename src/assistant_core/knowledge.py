"""Knowledge sources: the office directory (CSV) and the handbook (JSON)."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from assistant_core.errors import DataError


@dataclass(frozen=True)
class Office:
    """One campus office."""

    name: str
    room: str
    hours: str


class OfficeDirectory:
    """Offices loaded once from CSV, looked up by name."""

    def __init__(self, offices: dict[str, Office]):
        self._offices = offices

    @classmethod
    def from_csv(cls, path: Path) -> OfficeDirectory:
        try:
            with path.open(encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
        except FileNotFoundError as exc:
            raise DataError(f"office file not found: {path}") from exc
        try:
            offices = {r["name"].lower(): Office(r["name"], r["room"], r["hours"]) for r in rows}
        except KeyError as exc:
            raise DataError(f"office file missing column {exc}: {path}") from exc
        return cls(offices)

    @property
    def names(self) -> set[str]:
        return set(self._offices)

    def find(self, text: str) -> Office | None:
        t = text.lower()
        return next((o for name, o in self._offices.items() if name in t), None)


@dataclass(frozen=True)
class Rule:
    """One handbook rule; id and title become the answer's source."""

    id: str
    title: str
    text: str


class Handbook:
    """Handbook rules loaded once from JSON, searched by keyword overlap."""

    def __init__(self, rules: list[Rule]):
        self._rules = rules

    @classmethod
    def from_json(cls, path: Path) -> Handbook:
        try:
            with path.open(encoding="utf-8") as f:
                raw = json.load(f)
        except FileNotFoundError as exc:
            raise DataError(f"handbook file not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise DataError(f"handbook is not valid JSON: {exc}") from exc
        try:
            rules = [Rule(r["id"], r["title"], r["text"]) for r in raw]
        except KeyError as exc:
            raise DataError(f"handbook file missing column {exc}: {path}") from exc
        return cls(rules)

    def search(self, query: str) -> Rule | None:
        """Return the rule sharing the most long words (> 3 letters) with the query."""
        words = [w for w in query.lower().split() if len(w) > 3]
        best: Rule | None = None
        best_score = 0
        for rule in self._rules:
            score = sum(1 for w in words if w in rule.text.lower())
            if score > best_score:
                best = rule
                best_score = score
        return best
