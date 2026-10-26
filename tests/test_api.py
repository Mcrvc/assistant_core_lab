from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from assistant_core.api import create_app
from assistant_core.config import Settings
from assistant_core.knowledge import Handbook, OfficeDirectory
from assistant_core.responder import StubLLMResponder
from assistant_core.service import AssistantService

DATA = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("API_ADMIN_KEY", "secret-admin")
    settings = Settings(data_dir=DATA)
    offices = OfficeDirectory.from_csv(DATA / "offices.csv")
    handbook = Handbook.from_json(DATA / "handbook.json")
    service = AssistantService(settings, offices, handbook, StubLLMResponder())
    app = create_app(settings, service)
    return TestClient(app)


def test_list_feedback_unauthorized(client):
    r = client.get("/v1/feedback")
    assert r.status_code == 401


def test_list_feedback_wrong_key(client):
    r = client.get("/v1/feedback", headers={"X-API-Key": "wrong-key"})
    assert r.status_code == 401


def test_list_feedback_authorized(client):
    r = client.get("/v1/feedback", headers={"X-API-Key": "secret-admin"})
    assert r.status_code == 200
    assert r.json() == []
