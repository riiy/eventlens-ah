from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import JSON, UUID as SA_UUID
from sqlalchemy import String, Text, DateTime, Float
from sqlmodel import Field, SQLModel, Column


class RawDocument(SQLModel, table=True):
    __tablename__ = "raw_documents"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source: str = Field(sa_column=Column(String(255), index=True))
    source_type: str = Field(default="manual", sa_column=Column(String(50)))
    url: str | None = Field(default=None, sa_column=Column(String(2048)))
    title: str = Field(sa_column=Column(String(500)))
    content: str = Field(sa_column=Column(Text))
    language: str = Field(default="zh", sa_column=Column(String(10)))
    published_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), index=True))
    crawled_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    first_seen_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    content_hash: str = Field(sa_column=Column(String(64), unique=True, index=True))
    duplicate_group_id: UUID | None = Field(
        default=None,
        sa_column=Column(SA_UUID, index=True),
    )
    credibility_score: float = Field(default=0.5, sa_column=Column(Float))
    metadata_json: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))