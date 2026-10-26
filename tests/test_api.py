import httpx
import pytest
from fastapi.testclient import TestClient

from assistant_api.main import create_app
from assistant_api.weather import WeatherClient

OK_JSON = {"current": {"time": "2026-10-05T09:00", "temperature_2m": 31.2, "weather_code": 3, "wind_speed_10m": 8.5}}


def weather_with(handler) -> WeatherClient:
    transport = httpx.MockTransport(handler)
    return WeatherClient("https://example.test/forecast", 10.76, 106.68, retries=1, transport=transport)


@pytest.fixture
def client(settings, service):
    settings = settings.model_copy(update={"api_admin_key": "secret-admin", "rate_limit_per_min": 5})
    app = create_app(settings, service, weather_with(lambda req: httpx.Response(200, json=OK_JSON)))
    return TestClient(app)


def test_get_offices_returns_200(client):
    response = client.get("/v1/offices")
    assert response.status_code == 200


def test_get_offices_contains_library(client):
    response = client.get("/v1/offices")
    assert any(
        office["name"] == "Library"
        for office in response.json()
    )
