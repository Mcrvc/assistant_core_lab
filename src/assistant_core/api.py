"""HTTP API for the assistant (v1)."""

import os
import uuid

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status

from assistant_core.config import Settings
from assistant_core.knowledge import Handbook, OfficeDirectory
from assistant_core.models import ChatRequest, ChatResponse, FeedbackOut, Message
from assistant_core.responder import StubLLMResponder
from assistant_core.service import AssistantService


def create_app(settings: Settings | None = None, service: AssistantService | None = None) -> FastAPI:
    """Build the FastAPI app, wiring the Lab 3 service into the /v1/chat route."""
    settings = settings or Settings(data_dir="data")
    offices = OfficeDirectory.from_csv(settings.data_dir / "offices.csv")
    handbook = Handbook.from_json(settings.data_dir / "handbook.json")
    responder = StubLLMResponder()
    service = service or AssistantService(settings, offices, handbook, responder)

    feedback_store: list[FeedbackOut] = []

    app = FastAPI()

    def require_admin(x_api_key: str | None = Header(default=None)) -> None:
        admin_key = getattr(settings, "api_admin_key", None) or os.getenv("API_ADMIN_KEY", "change-me")
        if not admin_key or x_api_key != admin_key:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or invalid API key")

    @app.post("/v1/chat", response_model=ChatResponse)
    def chat(req: ChatRequest, request: Request) -> ChatResponse:
        resp = service.handle(Message(text=req.message, session_id=req.session_id))
        return ChatResponse(**resp.model_dump(), request_id=uuid.uuid4().hex[:12])

    # D.5 T3 — GET /v1/feedback, admin only (1 line)
    @app.get(
        "/v1/feedback",
        response_model=list[FeedbackOut],
        tags=["feedback"],
        dependencies=[Depends(require_admin)],
    )
    def list_feedback() -> list[FeedbackOut]:
        return feedback_store

    return app


app = create_app()
