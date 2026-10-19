from pathlib import Path

import pytest

from assistant_core.errors import DataError
from assistant_core.knowledge import Handbook, OfficeDirectory

DATA = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture
def offices() -> OfficeDirectory:
    return OfficeDirectory.from_csv(DATA / "offices.csv")


@pytest.fixture
def handbook() -> Handbook:
    return Handbook.from_json(DATA / "handbook.json")


def test_office_names_are_lowercase(offices):
    assert "library" in offices.names


def test_find_office_any_case(offices):
    o = offices.find("Where is the LIBRARY?")
    assert o is not None and o.room == "B.201"


def test_find_office_unknown(offices):
    assert offices.find("where is the cafeteria") is None


def test_search_matches_monolith(handbook):
    """Characterisation: the monolith answered this with source H26-5.3."""
    rule = handbook.search("can I register my thesis with 118 credits")
    assert rule is not None and rule.id == "H26-5.3"


def test_search_no_match(handbook):
    rule = handbook.search("pizza tonight")
    assert rule is None


def test_missing_office_file_raises(tmp_path):
    with pytest.raises(DataError):
        OfficeDirectory.from_csv(tmp_path / "nope.csv")


def test_bad_json_raises(tmp_path):
    bad = tmp_path / "handbook.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(DataError, match="not valid JSON"):
        Handbook.from_json(bad)
