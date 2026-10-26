"""Typed public request and response models."""

from datetime import datetime

from enum import Enum

from pydantic import BaseModel, Field


class Intent(str, Enum):
    """The supported categories of user request."""

    GREETING = "greeting"
    FEE = "fee"
    OFFICE = "office"
    RULE = "rule"
    UNKNOWN = "unknown"


class Message(BaseModel):
    """A validated message accepted by the service boundary."""

    text: str = Field(min_length=1, max_length=2000)
    session_id: str = "local"


class Source(BaseModel):
    """A knowledge item used to support an answer."""

    id: str
    title: str


class Response(BaseModel):
    """The structured result returned by the assistant service."""

    answer: str
    intent: Intent
    sources: list[Source] = Field(default_factory=list)
    degraded: bool = False


class ChatRequest(BaseModel):
    """A validated chat request accepted by the HTTP boundary."""

    message: str = Field(min_length=1, max_length=2000)
    session_id: str = "local"


class ChatResponse(BaseModel):
    """The structured chat reply returned to the caller."""

    answer: str
    intent: Intent
    sources: list[Source] = Field(default_factory=list)
    degraded: bool = False
    request_id: str


class FeedbackIn(BaseModel):
    request_id: str = Field(min_length=1, max_length=64)
    rating: int = Field(ge=-1, le=1)
    comment: str | None = Field(default=None, max_length=500)


class FeedbackOut(FeedbackIn):
    id: int
    created_at: datetime
class Weather(BaseModel):
    """Current campus weather, flagged when a stale cached value is used."""

    temperature_c: float
    wind_kmh: float
    description: str
    observed_at: str
    stale: bool = False
