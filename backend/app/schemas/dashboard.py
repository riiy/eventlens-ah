from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_documents: int
    total_events: int
    high_score_events: int
    pending_events: int
    event_type_distribution: dict[str, int]


class TopEventItem(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    event_type: str
    event_summary: str
    market_scope: str
    direction: str
    event_alpha_score: float
    created_at: datetime


class RecentDocumentItem(BaseModel):
    id: UUID
    source: str
    title: str
    published_at: datetime | None
    crawled_at: datetime | None