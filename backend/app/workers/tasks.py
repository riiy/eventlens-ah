"""Celery task definitions for asynchronous ingestion and extraction pipelines."""

import asyncio

from loguru import logger

from app.workers.celery_app import celery_app


@celery_app.task(name="run_extraction_pipeline")
def run_extraction_pipeline(document_ids: list[str]) -> dict:
    """Run the full extraction pipeline for one or more documents asynchronously.

    Each document goes through: extract events -> map assets -> score -> hypothesize.
    """

    async def _run() -> dict:
        from app.core.database import async_session_factory
        from app.ingestion.pipeline import IngestionPipeline

        results = []
        async with async_session_factory() as session:
            async with session.begin():
                pipeline = IngestionPipeline(session)
                for doc_id in document_ids:
                    try:
                        result = await pipeline.run_full_pipeline(doc_id)
                        results.append(result)
                    except Exception:
                        logger.exception("Pipeline failed for document {}", doc_id)
                        results.append(
                            {
                                "document_id": doc_id,
                                "event_id": None,
                                "error": "pipeline_failed",
                            }
                        )

        return {"processed": len(results), "results": results}

    return asyncio.run(_run())


@celery_app.task(name="run_demo_ingestion")
def run_demo_ingestion_task() -> dict:
    """Run the full demo ingestion pipeline asynchronously.

    Loads seed assets and documents, ingests each, and runs the extraction
    pipeline. This task is idempotent.
    """

    async def _run() -> dict:
        from app.core.database import async_session_factory
        from app.ingestion.pipeline import IngestionPipeline

        async with async_session_factory() as session:
            async with session.begin():
                pipeline = IngestionPipeline(session)
                return await pipeline.run_demo()

    return asyncio.run(_run())
