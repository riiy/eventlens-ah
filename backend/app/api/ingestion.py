"""API routes for the ingestion pipeline."""

from fastapi import APIRouter, Depends
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_pipeline
from app.ingestion.pipeline import IngestionPipeline
from app.schemas.ingestion import DemoIngestionResponse, ManualIngestionRequest
from app.schemas.raw_document import RawDocumentResponse

router = APIRouter(prefix="/api/ingestion", tags=["Ingestion"])


@router.post("/manual", response_model=RawDocumentResponse, status_code=201)
async def manual_ingestion(
    request: ManualIngestionRequest,
    session: AsyncSession = Depends(get_db),
    pipeline: IngestionPipeline = Depends(get_pipeline),
):
    """Ingest a single document manually and run the extraction pipeline.

    Accepts the same fields as RawDocumentCreate. The document is ingested
    and the full extraction pipeline (extract, map assets, score, hypothesize)
    is executed automatically.
    """
    # Build a dict compatible with the pipeline's ingest_document method
    doc_data = {
        "source": request.source,
        "source_type": request.source_type,
        "url": request.url,
        "title": request.title,
        "content": request.content,
        "language": request.language,
        "published_at": request.published_at,
    }

    doc = await pipeline.ingest_document(doc_data)
    await session.commit()
    await session.refresh(doc)

    # Run the full pipeline asynchronously (extract, map, score, hypothesize)
    try:
        await pipeline.run_full_pipeline(doc.id)
        await session.commit()
        await session.refresh(doc)
    except Exception:
        logger.exception("Pipeline failed for manually ingested document {}", doc.id)

    return doc


@router.post("/run-demo", response_model=DemoIngestionResponse)
async def run_demo_ingestion(
    session: AsyncSession = Depends(get_db),
    pipeline: IngestionPipeline = Depends(get_pipeline),
):
    """Run the full demo ingestion pipeline.

    Loads seed assets and documents, ingests each document, and runs
    the complete extraction pipeline. This endpoint is idempotent --
    running it multiple times will not create duplicate data.
    """
    result = await pipeline.run_demo()
    await session.commit()
    return DemoIngestionResponse(**result)
