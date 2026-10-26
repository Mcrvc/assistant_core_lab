"""HTTP API for the assistant (v1)."""

import uuid

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from assistant_core.config import Settings, load_settings
from assistant_core.knowledge import Handbook, OfficeDirectory
from assistant_core.models import ChatRequest, ChatResponse, FeedbackOut, Message, Weather
from assistant_core.responder import StubLLMResponder
from assistant_core.service import AssistantService
from assistant_core.weather import ExternalServiceError, WeatherClient


def create_app(
    settings: Settings | None = None,
    service: AssistantService | None = None,
    weather: WeatherClient | None = None,
) -> FastAPI:
    """Build the chat and campus weather API with injectable collaborators."""
    settings = settings or load_settings()
    offices = OfficeDirectory.from_csv(settings.data_dir / "offices.csv")
    handbook = Handbook.from_json(settings.data_dir / "handbook.json")
    responder = StubLLMResponder()
    service = service or AssistantService(settings, offices, handbook, responder)

    weather = weather or WeatherClient(
        settings.weather_url, settings.campus_lat, settings.campus_lon, timeout_s=settings.weather_timeout_s
    )
    feedback_store: list[FeedbackOut] = []

    app = FastAPI()

    def require_admin(x_api_key: str | None = Header(default=None)) -> None:
        if not settings.api_admin_key or x_api_key != settings.api_admin_key:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or invalid API key")

    @app.exception_handler(HTTPException)
    async def on_http(_: Request, exc: HTTPException) -> JSONResponse:
        message = str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": message.lower().replace(" ", "_"), "message": message}},
        )

    @app.post("/v1/chat", response_model=ChatResponse)
    def chat(req: ChatRequest, request: Request) -> ChatResponse:
        resp = service.handle(Message(text=req.message, session_id=req.session_id))
        return ChatResponse(**resp.model_dump(), request_id=uuid.uuid4().hex[:12])

    @app.get(
        "/v1/feedback",
        response_model=list[FeedbackOut],
        tags=["feedback"],
        dependencies=[Depends(require_admin)],
    )
    def list_feedback() -> list[FeedbackOut]:
        return feedback_store

    @app.get(
        "/v1/weather",
        response_model=Weather,
        tags=["external"],
        responses={503: {"description": "Weather unavailable"}},
    )
    def campus_weather() -> Weather:
        try:
            return weather.current()
        except ExternalServiceError:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Weather service unavailable") from None

    return app


app = create_app()
