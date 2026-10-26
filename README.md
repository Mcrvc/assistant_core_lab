# assistant_core_lab

The team application lives in `src/assistant_core/`. The `lab04/` directory
contains the course practice and starter materials.

## Setup (PowerShell, from this repository root)

Use Python 3.12 for the versions pinned in `requirements.txt`.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -e .
Copy-Item .env.example .env
```

## Run the root API

```powershell
.venv\Scripts\python.exe -m uvicorn assistant_core.api:app --reload
```

Open `http://127.0.0.1:8000/docs`. D6/T4 adds `GET /v1/weather`:

- `200`: current campus weather, including `temperature_c`, `wind_kmh`,
  `description`, `observed_at` and `stale`.
- If the upstream fails, a cached result is returned with `stale: true` when available.
- `503` when the upstream fails and no cached result exists:
  `{"error":{"code":"weather_service_unavailable","message":"Weather service unavailable"}}`.

The client uses a three-second timeout, one retry, and a ten-minute cache by default.
`WEATHER_URL`, `WEATHER_TIMEOUT_S`, `CAMPUS_LAT` and `CAMPUS_LON` are configured
through the environment or `.env`; no weather API key is required.

Part F (bonus) rate-limits `POST /v1/chat` per client IP: at most
`RATE_LIMIT_PER_MIN` requests (default 30) in any 60-second window. Extra requests get
`429` with `{"error":{"code":"too_many_requests","message":"Too many requests"}}`.
The counter lives in memory, so it resets when the server restarts.

## Test the root application

```powershell
.venv\Scripts\python.exe -m pytest -q tests
.venv\Scripts\python.exe -m pytest -q tests/test_api_weather.py
.venv\Scripts\python.exe -m pytest -q tests/test_api_ratelimit.py
```

The weather tests use `httpx.MockTransport` and run without internet access.
The tests inside `lab04/starter/` belong to the separate course starter project.
