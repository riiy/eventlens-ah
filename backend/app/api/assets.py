"""API routes for asset management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_asset_service, get_db
from app.models.asset import Asset
from app.models.event_asset_link import EventAssetLink
from app.models.market_event import MarketEvent
from app.schemas.asset import AssetCreate, AssetResponse
from app.schemas.common import PaginatedResponse
from app.schemas.market_event import MarketEventResponse
from app.services.asset_service import AssetService

router = APIRouter(prefix="/api/assets", tags=["Assets"])


@router.get("/", response_model=PaginatedResponse[AssetResponse])
async def list_assets(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    market: str | None = Query(default=None),
    sector: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
    service: AssetService = Depends(get_asset_service),
):
    """List assets with optional market and sector filters."""
    items, total = await service.list(
        session,
        offset=offset,
        limit=limit,
        market=market,
        sector=sector,
    )
    return PaginatedResponse(
        items=[AssetResponse.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("/", response_model=AssetResponse, status_code=201)
async def create_asset(
    data: AssetCreate,
    session: AsyncSession = Depends(get_db),
    service: AssetService = Depends(get_asset_service),
):
    """Create a new asset."""
    asset = await service.create(session, data)
    await session.commit()
    await session.refresh(asset)
    return asset


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: AssetService = Depends(get_asset_service),
):
    """Get a single asset by ID."""
    asset = await service.get(session, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.get("/{asset_id}/events", response_model=list[MarketEventResponse])
async def get_asset_events(
    asset_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    """Get all events linked to a specific asset."""
    asset_result = await session.execute(
        sa_select(Asset).where(Asset.id == asset_id)
    )
    if asset_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    result = await session.execute(
        sa_select(MarketEvent)
        .join(EventAssetLink, EventAssetLink.event_id == MarketEvent.id)
        .where(EventAssetLink.asset_id == asset_id)
        .order_by(MarketEvent.event_alpha_score.desc())
    )
    events = list(result.scalars().all())
    return [MarketEventResponse.model_validate(e) for e in events]
