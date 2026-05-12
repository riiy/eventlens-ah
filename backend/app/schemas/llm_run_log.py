from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LLMRunLogCreate(BaseModel):
    task_type: str
    model_name: str
    prompt_version: str = "v1"
    input_hash: str
    output_json: dict | None = None
    error_message: str | None = None
    latency_ms: int | None = None


class LLMRunLogResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    task_type: str
    model_name: str
    prompt_version: str
    input_hash: str
    output_json: dict | None
    error_message: str | None
    latency_ms: int | None
    success: bool
    created_at: datetime