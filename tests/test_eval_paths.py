"""Check Part F scoring, aggregation and the three service paths."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from assistant_core.config import Settings
from assistant_core.models import Intent, Message, Response, Source
from eval.compare_paths import build_paths, correct, evaluate

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("case", "response", "expected"),
    [
        (
            {"expect_source": "H26#5.3"},
            Response(answer="A rule.", intent=Intent.RULE, sources=[Source(id="H26#5.3", title="Thesis")]),
            True,
        ),
        (
            {"expect_source": "H26#5.3"},
            Response(answer="A rule.", intent=Intent.RULE, sources=[Source(id="H26#7.2", title="Exam")]),
            False,
        ),
        (
            {"expect_contains": "9,450,000"},
            Response(answer="Your tuition is 9,450,000 VND", intent=Intent.FEE),
            True,
        ),
        (
            {"expect_abstain": True},
            Response(answer="Unknown.", intent=Intent.UNKNOWN, path="abstain"),
            True,
        ),
        (
            {"expect_abstain": True},
            Response(answer="Unsupported answer.", intent=Intent.RULE, path="llm"),
            False,
        ),
    ],
)
def test_scoring_uses_the_expected_source_text_or_refusal(case, response, expected):
    assert correct(case, response) is expected


@pytest.fixture(scope="module")
def paths():
    return build_paths(Settings(data_dir=ROOT / "data", kb_dir=ROOT / "data/kb"))


@pytest.mark.parametrize(
    ("name", "expected_path"),
    [
        ("deterministic", "abstain"),
        ("retrieval", "retrieval"),
        ("llm (stub)", "llm"),
    ],
)
def test_comparison_paths_use_the_selected_answerer(paths, name, expected_path):
    response = paths[name].handle(Message(text="can I register my thesis with 118 credits"))
    assert response.path == expected_path
    if expected_path != "abstain":
        assert any(source.id == "H26#5.3" for source in response.sources)


def test_evaluation_counts_failures_and_refusals_separately():
    cases = [
        {"id": "T1", "question": "right source", "expect_source": "S26#1"},
        {"id": "T2", "question": "wrong source", "expect_source": "S26#1"},
        {"id": "T3", "question": "refuse", "expect_abstain": True},
        {"id": "T4", "question": "unsupported", "expect_abstain": True},
    ]
    responses = {
        "right source": Response(
            answer="A rule.", intent=Intent.RULE, sources=[Source(id="S26#1", title="Library")]
        ),
        "wrong source": Response(
            answer="Another rule.", intent=Intent.RULE, sources=[Source(id="S26#2", title="Password")]
        ),
        "refuse": Response(answer="Unknown.", intent=Intent.UNKNOWN, path="abstain"),
        "unsupported": Response(answer="Unsupported answer.", intent=Intent.RULE, path="llm"),
    }
    service = SimpleNamespace(handle=lambda message: responses[message.text])
    result = evaluate(service, cases)
    assert result["total"] == 4
    assert result["correct"] == 2
    assert result["abstain_total"] == 2
    assert result["abstain_ok"] == 1
    assert result["failures"] == ["T2", "T4"]
    assert 0 <= result["p50_ms"] <= result["max_ms"]


@pytest.mark.parametrize("name", ["deterministic", "retrieval", "llm (stub)"])
def test_comparison_paths_keep_the_fee_calculator(paths, name):
    response = paths[name].handle(Message(text="tuition for 18 credits and 2 retake"))
    assert response.intent == Intent.FEE
    assert response.path == "deterministic"
    assert "9,450,000" in response.answer
