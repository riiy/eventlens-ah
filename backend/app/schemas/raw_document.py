from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RawDocumentCreate(BaseModel):
    source: str
    source_type: str = "manual"
    url: str | None = None
    title: str
    content: str
    language: str = "zh"
    published_at: datetime | None = None


class RawDocumentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    source: str
    source_type: str
    url: str | None
    title: str
    content: str
    language: str
    published_at: datetime | None
    crawled_at: datetime | None
    first_seen_at: datetime | None = None
    created_at: datetime
    content_hash: str
    duplicate_group_id: UUID | None = None
    credibility_score: float


class RawDocumentListParams(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    source: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None