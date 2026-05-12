from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, Float, DateTime
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, SQLModel, Column


class Asset(SQLModel, table=True):
    __tablename__ = "assets"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    symbol: str = Field(sa_column=Column(String(20), unique=True, index=True))
    name: str = Field(sa_column=Column(String(255)))
    market: str = Field(sa_column=Column(String(20), index=True))
    exchange: str = Field(sa_column=Column(String(20)))
    sector: str | None = Field(default=None, sa_column=Column(String(100)))
    industry: str | None = Field(default=None, sa_column=Column(String(100)))
    business_tags: list | None = Field(default=None, sa_column=Column(JSON))
    liquidity_score: float = Field(default=0.5, sa_column=Column(Float))
    metadata_json: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))