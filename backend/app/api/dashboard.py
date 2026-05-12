"""API routes for the dashboard."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_dashboard_service, get_db
from app.schemas.dashboard import (
    DashboardSummary,
    RecentDocumentItem,
    TopEventItem,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    session: AsyncSession = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
):
    """Get a high-level summary of the system state."""
    summary = await service.get_summary(session)
    return DashboardSummary(**summary)


@router.get("/top-events", response_model=list[TopEventItem])
async def get_top_events(
    limit: int = Query(default=10, ge=1, le=50),
    session: AsyncSession = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
):
    """Get the top events ordered by event alpha score descending."""
    events = await service.get_top_events(session, limit=limit)
    return [TopEventItem.model_validate(e) for e in events]


@router.get("/recent-documents", response_model=list[RecentDocumentItem])
async def get_recent_documents(
    limit: int = Query(default=10, ge=1, le=50),
    session: AsyncSession = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
):
    """Get the most recently created documents."""
    docs = await service.get_recent_documents(session, limit=limit)
    return [RecentDocumentItem.model_validate(d) for d in docs]
