"""D6/T4 integration tests for the root assistant_core package; no real network."""

from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from assistant_core.api import create_app
from assistant_core.config import Settings
from assistant_core.weather import WeatherClient

DATA = Path(__file__).resolve().parents[1] / "data"
OK_JSON = {"current": {"time": "2026-10-05T09:00", "temperature_2m": 31.2, "weather_code": 3, "wind_speed_10m": 8.5}}


def weather_with(handler) -> WeatherClient:
    return WeatherClient(
        "https://example.test/forecast", 10.76, 106.68, retries=1, transport=httpx.MockTransport(handler)
    )


def client_with(weather: WeatherClient) -> TestClient:
    return TestClient(create_app(Settings(data_dir=DATA), weather=weather))


def test_weather_ok():
    client = client_with(weather_with(lambda req: httpx.Response(200, json=OK_JSON)))
    response = client.get("/v1/weather")
    assert response.status_code == 200
    assert response.json() == {
        "temperature_c": 31.2,
        "wind_kmh": 8.5,
        "description": "overcast",
        "observed_at": "2026-10-05T09:00",
        "stale": False,
    }


@pytest.mark.parametrize("failure", ["timeout", "http_error", "invalid_payload"])
def test_weather_failure_returns_503_after_retry(failure):
    calls = []

    def fail(request):
        calls.append(request)
        if failure == "timeout":
            raise httpx.ConnectTimeout("timeout", request=request)
        if failure == "http_error":
            return httpx.Response(500)
        return httpx.Response(200, json={"current": {}})

    response = client_with(weather_with(fail)).get("/v1/weather")
    assert len(calls) == 2
    assert response.status_code == 503
    assert response.json() == {
        "error": {"code": "weather_service_unavailable", "message": "Weather service unavailable"}
    }


def test_weather_stale_cache_when_upstream_fails():
    calls = []

    def flaky(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(200, json=OK_JSON)
        return httpx.Response(500)

    weather = weather_with(flaky)
    weather.cache_ttl_s = 0
    client = client_with(weather)
    fresh = client.get("/v1/weather")
    stale = client.get("/v1/weather")
    assert fresh.status_code == stale.status_code == 200
    assert fresh.json()["stale"] is False
    assert stale.json() == {**fresh.json(), "stale": True}
    assert len(calls) == 3


def test_chat_still_works_with_weather_enabled():
    client = client_with(weather_with(lambda req: httpx.Response(200, json=OK_JSON)))
    response = client.post("/v1/chat", json={"message": "hello"})
    assert response.status_code == 200
    assert response.json()["intent"] == "greeting"
    assert response.json()["request_id"]
