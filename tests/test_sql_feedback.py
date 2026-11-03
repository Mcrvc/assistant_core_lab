from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from sql.db import Feedback, Repository, init_db, make_engine

T0 = datetime(2026, 11, 3, 9, 0, tzinfo=timezone.utc)


def test_feedback_requires_an_interaction_and_survives_reopening(tmp_path):
    url = f"sqlite:///{(tmp_path / 'assistant.db').as_posix()}"
    engine = make_engine(url)
    init_db(engine)
    repo = Repository(engine, "test-salt")

    assert repo.add_feedback("missing", 1, None) is None

    repo.record_interaction("session", "req-1", "fee", None, True, False, 1.0)
    saved = repo.add_feedback("req-1", -1, "incorrect")
    assert saved.id == 1
    engine.dispose()

    reopened = make_engine(url)
    with Session(reopened) as db:
        feedback = db.exec(select(Feedback)).one()
        assert (feedback.request_id, feedback.rating, feedback.comment) == ("req-1", -1, "incorrect")
    reopened.dispose()


def repo_with_feedback(url: str, minutes_after_t0: list[int]) -> Repository:
    """One interaction + one feedback per entry; created_at is fixed so the order is deterministic."""
    engine = make_engine(url)
    init_db(engine)
    repo = Repository(engine, "test-salt")
    for minutes in minutes_after_t0:
        repo.record_interaction("session", f"req-{minutes}", "fee", None, True, False, 1.0)
    with Session(engine) as db:
        for minutes in minutes_after_t0:
            db.add(Feedback(request_id=f"req-{minutes}", rating=1, created_at=T0 + timedelta(minutes=minutes)))
        db.commit()
    return repo


def test_list_feedback_newest_first():
    repo = repo_with_feedback("sqlite://", [5, 1, 10])  # inserted out of order on purpose
    assert [fb.request_id for fb in repo.list_feedback()] == ["req-10", "req-5", "req-1"]


def test_list_feedback_respects_limit():
    repo = repo_with_feedback("sqlite://", [1, 2, 3])
    assert [fb.request_id for fb in repo.list_feedback(limit=2)] == ["req-3", "req-2"]


def test_list_feedback_empty_database():
    engine = make_engine("sqlite://")
    init_db(engine)
    assert Repository(engine, "test-salt").list_feedback() == []


def test_list_feedback_survives_reopening(tmp_path):
    url = f"sqlite:///{(tmp_path / 'assistant.db').as_posix()}"
    repo_with_feedback(url, [1, 2]).engine.dispose()

    reopened = Repository(make_engine(url), "test-salt")
    assert [fb.request_id for fb in reopened.list_feedback()] == ["req-2", "req-1"]
    reopened.engine.dispose()
