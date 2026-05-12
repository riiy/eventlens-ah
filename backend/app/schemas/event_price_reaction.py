from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EventPriceReactionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    event_id: UUID
    asset_id: UUID
    return_1d: float | None
    return_3d: float | None
    return_5d: float | None
    return_20d: float | None
    max_drawdown: float | None
    volume_change: float | None
    benchmark_return: float | None
    excess_return: float | None
    notes: str | None
    created_at: datetime