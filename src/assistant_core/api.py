"""HTTP API for the assistant (v1)."""

import uuid

from fastapi import FastAPI, Request

from assistant_core.config import Settings
from assistant_core.knowledge import Handbook, OfficeDirectory
from assistant_core.models import ChatRequest, ChatResponse, Message
from assistant_core.responder import StubLLMResponder
from assistant_core.service import AssistantService


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

    return app


app = create_app()
