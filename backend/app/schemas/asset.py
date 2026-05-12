from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AssetCreate(BaseModel):
    symbol: str
    name: str
    market: str
    exchange: str
    sector: str | None = None
    industry: str | None = None
    business_tags: list[str] | None = None


class AssetResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    symbol: str
    name: str
    market: str
    exchange: str
    sector: str | None
    industry: str | None
    business_tags: list[str] | None
    created_at: datetime
    liquidity_score: float | None = None


class AssetListParams(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    market: str | None = None
    sector: str | None = None