"""Dependency injection functions for FastAPI routes."""

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.ingestion.pipeline import IngestionPipeline
from app.llm import get_llm_provider
from app.llm.base import BaseLLMProvider
from app.services.asset_service import AssetService
from app.services.dashboard_service import DashboardService
from app.services.document_service import DocumentService
from app.services.event_service import EventService
from app.services.hypothesis_service import HypothesisService


async def get_db(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    """Yield an async database session."""
    yield session


def get_doc_service() -> DocumentService:
    """Return a singleton DocumentService instance."""
    return DocumentService()


def get_event_service() -> EventService:
    """Return a singleton EventService instance."""
    return EventService()


def get_asset_service() -> AssetService:
    """Return a singleton AssetService instance."""
    return AssetService()


def get_dashboard_service() -> DashboardService:
    """Return a singleton DashboardService instance."""
    return DashboardService()


def get_hypothesis_service() -> HypothesisService:
    """Return a singleton HypothesisService instance."""
    return HypothesisService()


def get_llm() -> BaseLLMProvider:
    """Return the configured LLM provider."""
    return get_llm_provider()


async def get_pipeline(
    session: AsyncSession = Depends(get_db),
) -> IngestionPipeline:
    """Return an IngestionPipeline bound to the current database session."""
    return IngestionPipeline(session)
