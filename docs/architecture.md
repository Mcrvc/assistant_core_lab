# Architecture — assistant_core

## Module table

| Module | Responsibility |
|--------|----------------|
| `config.py` | Read settings from the environment; validate with Pydantic. |
| `errors.py` | Named exceptions: `AssistantError`, `ConfigError`, `DataError`, `InvalidRequest`, `ProviderError`. |
| `models.py` | Public contract: `Intent`, `Message`, `Response`, `Source`. |
| `router.py` | Choose an `Intent` with simple rules. |
| `knowledge.py` | Office directory (CSV) and handbook (JSON) with search. |
| `tools.py` | Deterministic tuition calculation (pure functions, no I/O). |
| `responder.py` | Response generation behind one interface (stub LLM, template fallback). |
| `service.py` | `AssistantService.handle(Message) -> Response` — the only entry point. |
| `logging_setup.py` | Structured JSON logs to stderr. |
| `__main__.py` | Command-line interface. |
| `api.py` | FastAPI routes for chat and campus weather; HTTP error responses. |
| `weather.py` | Open-Meteo client with timeout, retry and stale-cache fallback. |

## Service interface

`AssistantService.handle(msg: Message) -> Response`

- `Message`: `text` (1–2000 chars), `session_id`
- `Response`: `answer`, `intent`, `sources[]`, `degraded` (True if a fallback was used)
- Errors: invalid input -> `ValidationError`; startup -> `ConfigError` / `DataError`; provider failures never reach the caller (fallback instead)

The CLI today, the FastAPI backend in Lab 4 and the UI in Lab 7 all call this one method. That is what makes the service maintainable.

## Decisions

- **Fees are computed in `tools.py`, never by an LLM.** Exact, testable, deterministic results instead of non-deterministic AI output.
- **The LLM sits behind `Responder`; the stub needs no API key.** Tests and CI run offline without secrets; a real provider can be added in Week 4 without changing the service.
- **Configuration comes from the environment; `.env.example` documents every variable.** No secrets or settings hard-coded in source; `.env` is never committed.
