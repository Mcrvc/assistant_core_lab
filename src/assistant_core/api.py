"""HTTP API for the assistant (v1)."""

import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

from assistant_core.config import Settings
from assistant_core.knowledge import Handbook, OfficeDirectory
from assistant_core.models import ChatRequest, ChatResponse, Message
from assistant_core.responder import StubLLMResponder
from assistant_core.service import AssistantService


class FeedbackIn(BaseModel):
    request_id: str = Field(min_length=1, max_length=64)
    rating: int = Field(ge=-1, le=1)
    comment: str | None = Field(default=None, max_length=500)


class FeedbackOut(FeedbackIn):
    id: int
    created_at: datetime


def create_app(settings: Settings | None = None, service: AssistantService | None = None) -> FastAPI:
    """Build the FastAPI app, wiring the Lab 3 service into the /v1/chat route."""
    settings = settings or Settings(data_dir="data")
    offices = OfficeDirectory.from_csv(settings.data_dir / "offices.csv")
    handbook = Handbook.from_json(settings.data_dir / "handbook.json")
    responder = StubLLMResponder()
    service = service or AssistantService(settings, offices, handbook, responder)

    app = FastAPI()

    @app.post("/v1/chat", response_model=ChatResponse)
    def chat(req: ChatRequest, request: Request) -> ChatResponse:
        resp = service.handle(Message(text=req.message, session_id=req.session_id))
        return ChatResponse(**resp.model_dump(), request_id=uuid.uuid4().hex[:12])

    feedback_store: list[FeedbackOut] = []

    @app.post("/v1/feedback", response_model=FeedbackOut, status_code=201, tags=["feedback"])
    def add_feedback(fb: FeedbackIn) -> FeedbackOut:
        item = FeedbackOut(**fb.model_dump(), id=len(feedback_store) + 1, created_at=datetime.now(timezone.utc))
        feedback_store.append(item)
        return item

    return app


app = create_app()
