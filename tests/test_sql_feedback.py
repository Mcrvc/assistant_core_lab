from sqlmodel import Session, select

from sql.db import Feedback, Repository, init_db, make_engine


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
