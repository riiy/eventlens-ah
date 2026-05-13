from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, Text, Float, DateTime
from sqlmodel import Field, SQLModel, Column


class EventPriceReaction(SQLModel, table=True):
    __tablename__ = "event_price_reactions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    event_id: UUID = Field(foreign_key="market_events.id", index=True)
    asset_id: UUID = Field(foreign_key="assets.id")
    return_1d: float | None = Field(default=None, sa_column=Column(Float))
    return_3d: float | None = Field(default=None, sa_column=Column(Float))
    return_5d: float | None = Field(default=None, sa_column=Column(Float))
    return_20d: float | None = Field(default=None, sa_column=Column(Float))
    max_drawdown: float | None = Field(default=None, sa_column=Column(Float))
    volume_change: float | None = Field(default=None, sa_column=Column(Float))
    benchmark_return: float | None = Field(default=None, sa_column=Column(Float))
    excess_return: float | None = Field(default=None, sa_column=Column(Float))
    notes: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    asset_name: str = Field(default="", sa_column=Column(String(255)))
    asset_symbol: str = Field(default="", sa_column=Column(String(50)))