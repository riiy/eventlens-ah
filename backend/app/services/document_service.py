import hashlib
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.raw_document import RawDocument
from app.schemas.raw_document import RawDocumentCreate


class DocumentService:
    """Service for managing RawDocument CRUD operations."""

    async def create(
        self, session: AsyncSession, data: RawDocumentCreate
    ) -> RawDocument:
        """Create a new RawDocument, deduplicating by content_hash.

        If a document with the same content_hash already exists, returns the
        existing document instead of creating a duplicate.
        """
        content_hash = hashlib.sha256(data.content.encode("utf-8")).hexdigest()

        # Check for existing document with the same hash
        result = await session.execute(
            select(RawDocument).where(RawDocument.content_hash == content_hash)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            logger.debug(
                "Document with content_hash={} already exists (id={}), skipping",
                content_hash,
                existing.id,
            )
            return existing

        doc = RawDocument(
            source=data.source,
            source_type=data.source_type,
            url=data.url,
            title=data.title,
            content=data.content,
            language=data.language,
            published_at=data.published_at,
            content_hash=content_hash,
        )
        session.add(doc)
        await session.flush()
        logger.info("Created RawDocument id={} hash={}", doc.id, content_hash)
        return doc

    async def get(
        self, session: AsyncSession, doc_id: UUID
    ) -> RawDocument | None:
        """Get a single RawDocument by ID."""
        result = await session.execute(
            select(RawDocument).where(RawDocument.id == doc_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        session: AsyncSession,
        offset: int = 0,
        limit: int = 20,
        source: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> tuple[list[RawDocument], int]:
        """List RawDocuments with optional filtering and pagination.

        Returns a tuple of (items, total_count).
        """
        conditions = []

        if source is not None:
            conditions.append(RawDocument.source == source)
        if date_from is not None:
            conditions.append(RawDocument.created_at >= date_from)
        if date_to is not None:
            conditions.append(RawDocument.created_at <= date_to)

        # Count query
        count_stmt = select(func.count()).select_from(RawDocument)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Items query
        items_stmt = (
            select(RawDocument)
            .order_by(RawDocument.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if conditions:
            items_stmt = items_stmt.where(*conditions)
        items_result = await session.execute(items_stmt)
        items = list(items_result.scalars().all())

        return items, total
