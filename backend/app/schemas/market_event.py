from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MarketEventCreate(BaseModel):
    raw_document_id: UUID
    event_type: str
    event_summary: str
    primary_entity: str | None = None
    related_entities: list[str] = Field(default_factory=list)
    market_scope: str
    direction: str


class MarketEventResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    raw_document_id: UUID
    event_type: str
    event_summary: str
    primary_entity: str | None
    related_entities: list[str]
    market_scope: str
    direction: str
    materiality_score: float | None = None
    novelty_score: float | None = None
    urgency_score: float | None = None
    credibility_score: float | None = None
    confidence_score: float | None = None
    risk_score: float | None = None
    event_alpha_score: float | None = None
    first_seen_at: datetime | None = None
    status: str
    created_at: datetime


class MarketEventListParams(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    event_type: str | None = None
    market_scope: str | None = None
    direction: str | None = None
    status: str | None = None
    min_score: float | None = None
    max_score: float | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


class ExtractEventsRequest(BaseModel):
    document_ids: list[UUID]


class ScoreEventRequest(BaseModel):
    event_id: UUID


class GenerateHypothesisRequest(BaseModel):
    event_id: UUID