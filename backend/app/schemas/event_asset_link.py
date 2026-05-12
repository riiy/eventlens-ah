from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EventAssetLinkResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    event_id: UUID
    asset_id: UUID
    symbol: str | None = None
    name: str | None = None
    impact_direction: str
    impact_strength: float
    reason: str | None
    confidence_score: float | None
    created_at: datetime