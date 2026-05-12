from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSON, UUID as SA_UUID
from sqlmodel import Field, SQLModel, Column


class ResearchHypothesis(SQLModel, table=True):
    __tablename__ = "research_hypotheses"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    event_id: UUID = Field(sa_column=Column(SA_UUID, index=True))
    hypothesis_text: str = Field(sa_column=Column(Text))
    impact_chain: list | None = Field(default=None, sa_column=Column(JSON))
    supporting_evidence: list | None = Field(default=None, sa_column=Column(JSON))
    counter_evidence: list | None = Field(default=None, sa_column=Column(JSON))
    trigger_conditions: list | None = Field(default=None, sa_column=Column(JSON))
    invalidation_conditions: list | None = Field(default=None, sa_column=Column(JSON))
    time_horizon: str = Field(sa_column=Column(String(50)))
    risk_notes: str | None = Field(default=None, sa_column=Column(Text))
    model_used: str = Field(default="mock", sa_column=Column(String(100)))
    status: str = Field(
        default="ACTIVE",
        sa_column=Column(String(20)),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))