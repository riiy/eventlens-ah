from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, Text, Float, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel, Column


class EventAssetLink(SQLModel, table=True):
    __tablename__ = "event_asset_links"
    __table_args__ = (
        UniqueConstraint("event_id", "asset_id", name="uq_event_asset_link"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    event_id: UUID = Field(foreign_key="market_events.id")
    asset_id: UUID = Field(foreign_key="assets.id")
    impact_direction: str = Field(sa_column=Column(String(20)))
    impact_strength: float = Field(default=0.0, sa_column=Column(Float))
    reason: str = Field(sa_column=Column(Text))
    confidence_score: float = Field(default=0.0, sa_column=Column(Float))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))