from datetime import datetime

from pydantic import BaseModel


class ManualIngestionRequest(BaseModel):
    source: str
    source_type: str = "manual"
    url: str | None = None
    title: str
    content: str
    language: str = "zh"
    published_at: datetime | None = None


class DemoIngestionResponse(BaseModel):
    assets_created: int
    documents_ingested: int
    events_extracted: int
    message: str