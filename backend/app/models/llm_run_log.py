from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, SQLModel, Column


class LLMRunLog(SQLModel, table=True):
    __tablename__ = "llm_run_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_type: str = Field(sa_column=Column(String(100), index=True))
    model_name: str = Field(sa_column=Column(String(100)))
    prompt_version: str = Field(default="v1", sa_column=Column(String(20)))
    input_hash: str = Field(sa_column=Column(String(64), index=True))
    output_json: dict | None = Field(default=None, sa_column=Column(JSON))
    error_message: str | None = Field(default=None, sa_column=Column(Text))
    latency_ms: int | None = Field(default=None, sa_column=Column(Integer))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))