"""Lab 4 Part F (bonus): rate limiting on POST /v1/chat; no real network."""

from pathlib import Path

from fastapi.testclient import TestClient

from assistant_core import ratelimit
from assistant_core.api import create_app
from assistant_core.config import Settings, load_settings
from assistant_core.ratelimit import RateLimiter

DATA = Path(__file__).resolve().parents[1] / "data"


def client_with_limit(per_minute: int) -> TestClient:
    return TestClient(create_app(Settings(data_dir=DATA, rate_limit_per_min=per_minute)))


def test_chat_returns_429_after_limit():
    client = client_with_limit(5)
    responses = [client.post("/v1/chat", json={"message": "hi"}) for _ in range(6)]
    assert [r.status_code for r in responses[:5]] == [200] * 5
    assert responses[-1].status_code == 429
    assert responses[-1].json() == {"error": {"code": "too_many_requests", "message": "Too many requests"}}


def test_limit_is_per_client():
    limiter = RateLimiter(per_minute=1)
    assert limiter.allow("10.0.0.1")
    assert not limiter.allow("10.0.0.1")
    assert limiter.allow("10.0.0.2")


def test_limit_resets_after_one_minute(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(ratelimit.time, "monotonic", lambda: now[0])
    limiter = RateLimiter(per_minute=2)
    assert limiter.allow("a") and limiter.allow("a")
    assert not limiter.allow("a")
    now[0] += 61
    assert limiter.allow("a")


def test_rate_limit_read_from_environment(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MIN", "7")
    assert load_settings(env_file=None).rate_limit_per_min == 7
