from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, Text, DateTime, Float
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, SQLModel, Column


class MarketEvent(SQLModel, table=True):
    __tablename__ = "market_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    raw_document_id: UUID = Field(foreign_key="raw_documents.id")
    event_type: str = Field(sa_column=Column(String(100), index=True))
    event_summary: str = Field(sa_column=Column(Text))
    primary_entity: str | None = Field(default=None, sa_column=Column(String(255)))
    related_entities: list | None = Field(default=None, sa_column=Column(JSON))
    market_scope: str = Field(default="UNKNOWN", sa_column=Column(String(20)))
    direction: str = Field(default="UNKNOWN", sa_column=Column(String(20)))
    materiality_score: float = Field(default=0.0, sa_column=Column(Float))
    novelty_score: float = Field(default=0.0, sa_column=Column(Float))
    urgency_score: float = Field(default=0.0, sa_column=Column(Float))
    credibility_score: float = Field(default=0.0, sa_column=Column(Float))
    confidence_score: float = Field(default=0.0, sa_column=Column(Float))
    risk_score: float = Field(default=0.0, sa_column=Column(Float))
    event_alpha_score: float = Field(default=0.0, sa_column=Column(Float))
    first_seen_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    status: str = Field(default="EXTRACTED", sa_column=Column(String(20)))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))