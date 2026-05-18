"""API routes for market event management and the event extraction pipeline."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_db,
    get_event_service,
    get_hypothesis_service,
)
from app.models.event_asset_link import EventAssetLink
from app.models.llm_run_log import LLMRunLog
from app.schemas.common import PaginatedResponse
from app.schemas.event_asset_link import EventAssetLinkResponse
from app.schemas.event_price_reaction import EventPriceReactionResponse
from app.schemas.llm_run_log import LLMRunLogResponse
from app.schemas.market_event import (
    ExtractEventsRequest,
    MarketEventResponse,
)
from app.schemas.research_hypothesis import ResearchHypothesisResponse
from app.services.event_service import EventService
from app.services.hypothesis_service import HypothesisService

router = APIRouter(prefix="/api/events", tags=["Events"])


@router.get("/", response_model=PaginatedResponse[MarketEventResponse])
async def list_events(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    event_type: str | None = Query(default=None),
    market_scope: str | None = Query(default=None),
    direction: str | None = Query(default=None),
    status: str | None = Query(default=None),
    min_score: float | None = Query(default=None),
    max_score: float | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    session: AsyncSession = Depends(get_db),
    service: EventService = Depends(get_event_service),
):
    """List market events with comprehensive filtering and sorting."""
    items, total = await service.list(
        session,
        offset=offset,
        limit=limit,
        event_type=event_type,
        market_scope=market_scope,
        direction=direction,
        status=status,
        min_score=min_score,
        max_score=max_score,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return PaginatedResponse(
        items=[MarketEventResponse.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{event_id}", response_model=MarketEventResponse)
async def get_event(
    event_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: EventService = Depends(get_event_service),
):
    """Get a single market event by ID."""
    event = await service.get(session, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post(
    "/extract",
    response_model=list[MarketEventResponse],
    status_code=201,
)
async def extract_events(
    request: ExtractEventsRequest,
    session: AsyncSession = Depends(get_db),
    service: EventService = Depends(get_event_service),
):
    """Extract market events from one or more raw documents using the LLM."""
    if not request.document_ids:
        raise HTTPException(
            status_code=400, detail="At least one document_id is required"
        )

    extracted_events = []
    for doc_id in request.document_ids:
        event = await service.extract_from_document(session, doc_id)
        if event is not None:
            extracted_events.append(event)

    await session.commit()
    for event in extracted_events:
        await session.refresh(event)

    return [
        MarketEventResponse.model_validate(e) for e in extracted_events
    ]


@router.post(
    "/{event_id}/score",
    response_model=MarketEventResponse,
)
async def score_event(
    event_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: EventService = Depends(get_event_service),
):
    """Score a market event using the EventAlphaScorer."""
    scored = await service.score(session, event_id)
    if scored is None:
        raise HTTPException(status_code=404, detail="Event not found")

    await session.commit()
    await session.refresh(scored)
    return scored


@router.post(
    "/{event_id}/generate-hypothesis",
    response_model=ResearchHypothesisResponse,
)
async def generate_hypothesis(
    event_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: EventService = Depends(get_event_service),
):
    """Generate an investment research hypothesis for an event using the LLM."""
    logger.info("API call: generate_hypothesis for event_id={}", event_id)
    hypothesis = await service.generate_hypothesis(session, event_id)
    if hypothesis is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found or no linked assets available",
        )

    await session.commit()
    await session.refresh(hypothesis)
    return hypothesis


@router.get(
    "/{event_id}/assets",
    response_model=list[EventAssetLinkResponse],
)
async def get_event_assets(
    event_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: EventService = Depends(get_event_service),
):
    """Get all asset links for a specific event, including asset symbol/name."""
    event = await service.get(session, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    from sqlalchemy import select as sa_select
    from app.models.asset import Asset

    result = await session.execute(
        sa_select(EventAssetLink, Asset.symbol, Asset.name)
        .join(Asset, EventAssetLink.asset_id == Asset.id)
        .where(EventAssetLink.event_id == event_id)
    )
    rows = result.all()
    links = []
    for link, symbol, name in rows:
        link_data = {
            "id": link.id,
            "event_id": link.event_id,
            "asset_id": link.asset_id,
            "symbol": symbol,
            "name": name,
            "impact_direction": link.impact_direction,
            "impact_strength": link.impact_strength,
            "reason": link.reason,
            "confidence_score": link.confidence_score,
            "created_at": link.created_at,
        }
        links.append(EventAssetLinkResponse.model_validate(link_data))
    return [EventAssetLinkResponse.model_validate(link) for link in links]


@router.post(
    "/{event_id}/map-assets",
    response_model=list[EventAssetLinkResponse],
    status_code=201,
)
async def map_event_assets(
    event_id: UUID,
    session: AsyncSession = Depends(get_db),
    service: EventService = Depends(get_event_service),
):
    """Map a market event to relevant assets using the LLM."""
    event = await service.get(session, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    links = await service.map_assets(session, event_id)
    await session.commit()

    if not links:
        return []

    asset_ids = [link.asset_id for link in links]
    from sqlalchemy import select as sa_select
    from app.models.asset import Asset

    assets_result = await session.execute(
        sa_select(Asset).where(Asset.id.in_(asset_ids))
    )
    asset_map = {a.id: a for a in assets_result.scalars().all()}

    enriched = []
    for link in links:
        asset = asset_map.get(link.asset_id)
        enriched.append(EventAssetLinkResponse.model_validate({
            "id": link.id,
            "event_id": link.event_id,
            "asset_id": link.asset_id,
            "symbol": asset.symbol if asset else None,
            "name": asset.name if asset else None,
            "impact_direction": link.impact_direction,
            "impact_strength": link.impact_strength,
            "reason": link.reason,
            "confidence_score": link.confidence_score,
            "created_at": link.created_at,
        }))
    return enriched


@router.get(
    "/{event_id}/hypotheses",
    response_model=list[ResearchHypothesisResponse],
)
async def get_event_hypotheses(
    event_id: UUID,
    session: AsyncSession = Depends(get_db),
    event_service: EventService = Depends(get_event_service),
    hypothesis_service: HypothesisService = Depends(get_hypothesis_service),
):
    """Get all research hypotheses for a specific event."""
    event = await event_service.get(session, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    hypotheses = await hypothesis_service.get_for_event(session, event_id)
    return [
        ResearchHypothesisResponse.model_validate(h) for h in hypotheses
    ]


@router.get(
    "/{event_id}/price-reactions",
    response_model=list[EventPriceReactionResponse],
)
async def get_event_price_reactions(
    event_id: UUID,
    session: AsyncSession = Depends(get_db),
    event_service: EventService = Depends(get_event_service),
    hypothesis_service: HypothesisService = Depends(get_hypothesis_service),
):
    """Get all price reactions for a specific event."""
    event = await event_service.get(session, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    reactions = await hypothesis_service.get_price_reactions(session, event_id)
    return [
        EventPriceReactionResponse.model_validate(r) for r in reactions
    ]


@router.post(
    "/{event_id}/price-reactions",
    response_model=list[EventPriceReactionResponse],
    status_code=201,
)
async def generate_mock_price_reactions(
    event_id: UUID,
    session: AsyncSession = Depends(get_db),
    event_service: EventService = Depends(get_event_service),
    hypothesis_service: HypothesisService = Depends(get_hypothesis_service),
):
    """Generate mock price reaction data for an event based on linked assets."""
    event = await event_service.get(session, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    reactions = await hypothesis_service.generate_mock_price_reactions(session, event_id)
    await session.commit()
    return [
        EventPriceReactionResponse.model_validate(r) for r in reactions
    ]


@router.get(
    "/{event_id}/llm-runs",
    response_model=list[LLMRunLogResponse],
)
async def get_event_llm_runs(
    event_id: UUID,
    session: AsyncSession = Depends(get_db),
    event_service: EventService = Depends(get_event_service),
):
    """Get all LLM run logs related to an event's pipeline execution."""
    event = await event_service.get(session, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    from datetime import timedelta
    window_start = event.created_at - timedelta(seconds=10)
    window_end = event.created_at + timedelta(seconds=30)

    result = await session.execute(
        select(LLMRunLog)
        .where(
            LLMRunLog.created_at >= window_start,
            LLMRunLog.created_at <= window_end,
        )
        .order_by(LLMRunLog.created_at.asc())
    )
    logs = list(result.scalars().all())
    return [LLMRunLogResponse.model_validate(l) for l in logs]
