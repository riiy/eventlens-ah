from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ResearchHypothesisResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    event_id: UUID
    hypothesis_text: str
    impact_chain: list[str] | None
    supporting_evidence: list[str] | None
    counter_evidence: list[str] | None
    trigger_conditions: list[str] | None
    invalidation_conditions: list[str] | None
    time_horizon: str | None = None
    risk_notes: str | None = None
    model_used: str | None = None
    status: str
    created_at: datetime