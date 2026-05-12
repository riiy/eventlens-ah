"""API routes for raw document management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_doc_service
from app.schemas.common import PaginatedResponse
from app.schemas.raw_document import (
    RawDocumentCreate,
    RawDocumentResponse,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/raw-documents", tags=["Documents"])


@router.post("/", response_model=RawDocumentResponse, status_code=201)
async def create_document(
    data: RawDocumentCreate,
    session: AsyncSession = Depends(get_db),
    service: DocumentService = Depends(get_doc_service),
):
    """Create a new raw document. Deduplicates by content hash."""
    doc = await service.create(session, data)
    await session.commit()
    await session.refresh(doc)
    return doc


@router.get("/", response_model=PaginatedResponse[RawDocumentResponse])
async def list_documents(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    source: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
    service: DocumentService = Depends(get_doc_service),
):
    """List raw documents with pagination and optional filters."""
    items, total = await service.list(
        session,
        offset=offset,
        limit=limit,
        source=source,
        date_from=date_from,
        date_to=date_to,
    )
    return PaginatedResponse(
        items=[RawDocumentResponse.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{document_id}", response_model=RawDocumentResponse)
async def get_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: DocumentService = Depends(get_doc_service),
):
    """Get a single raw document by ID."""
    doc = await service.get(session, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
