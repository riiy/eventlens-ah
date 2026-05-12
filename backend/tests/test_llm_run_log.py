import pytest
from uuid import uuid4

from app.models.asset import Asset
from app.models.event_asset_link import EventAssetLink
from app.models.llm_run_log import LLMRunLog
from app.models.market_event import MarketEvent
from app.models.raw_document import RawDocument
from app.services.event_service import EventService
from sqlalchemy import select


async def _create_doc_and_event(session):
    """Helper: create a document and an extracted event from it."""
    doc = RawDocument(
        source="test_source",
        title="茅台宣布提价20% 利好白酒板块",
        content="贵州茅台宣布上调出厂价约20%，这是时隔6年的首次提价...",
        language="zh",
    )
    session.add(doc)
    await session.flush()

    event = MarketEvent(
        raw_document_id=doc.id,
        event_type="earnings_surprise",
        event_summary="茅台提价20%",
        primary_entity="贵州茅台",
        market_scope="A_SHARE",
        direction="POSITIVE",
    )
    session.add(event)
    await session.flush()
    return event


@pytest.mark.asyncio
async def test_extract_from_document_records_llm_run_log(async_session):
    doc = RawDocument(
        source="test_source",
        title="茅台宣布提价20% 利好白酒板块",
        content="贵州茅台宣布上调出厂价约20%，这是时隔6年的首次提价...",
        language="zh",
    )
    async_session.add(doc)
    await async_session.flush()

    service = EventService()
    event = await service.extract_from_document(async_session, doc.id)

    assert event is not None
    result = await async_session.execute(
        select(LLMRunLog).where(LLMRunLog.task_type == "extract_event")
    )
    logs = list(result.scalars().all())
    assert len(logs) == 1
    log = logs[0]
    assert log.model_name == "mock"
    assert log.prompt_version == "v1"
    assert log.output_json is not None
    assert log.error_message is None
    assert log.latency_ms is not None
    assert log.latency_ms >= 0
    assert log.success is True


@pytest.mark.asyncio
async def test_map_assets_records_llm_run_log(async_session):
    event = await _create_doc_and_event(async_session)

    asset = Asset(
        symbol="600519.SH", name="贵州茅台", market="A_SHARE", exchange="SSE",
    )
    async_session.add(asset)
    await async_session.flush()

    service = EventService()
    links = await service.map_assets(async_session, event.id)

    assert len(links) >= 1
    result = await async_session.execute(
        select(LLMRunLog).where(LLMRunLog.task_type == "map_assets")
    )
    logs = list(result.scalars().all())
    assert len(logs) == 1
    log = logs[0]
    assert log.model_name == "mock"
    assert log.output_json is not None
    assert log.error_message is None
    assert log.success is True


@pytest.mark.asyncio
async def test_generate_hypothesis_records_llm_run_log(async_session):
    event = await _create_doc_and_event(async_session)

    asset = Asset(
        symbol="600519.SH", name="贵州茅台", market="A_SHARE", exchange="SSE",
    )
    async_session.add(asset)
    await async_session.flush()

    link = EventAssetLink(
        event_id=event.id, asset_id=asset.id,
        impact_direction="POSITIVE", impact_strength=0.8,
        reason="直接相关", confidence_score=0.9,
    )
    async_session.add(link)
    await async_session.flush()

    service = EventService()
    hypothesis = await service.generate_hypothesis(async_session, event.id)

    assert hypothesis is not None
    result = await async_session.execute(
        select(LLMRunLog).where(LLMRunLog.task_type == "generate_hypothesis")
    )
    logs = list(result.scalars().all())
    assert len(logs) == 1
    log = logs[0]
    assert log.model_name == "mock"
    assert log.output_json is not None
    assert log.error_message is None
    assert log.success is True


@pytest.mark.asyncio
async def test_extract_from_document_not_found_no_log(async_session):
    service = EventService()
    result = await service.extract_from_document(async_session, uuid4())
    assert result is None

    result = await async_session.execute(select(LLMRunLog))
    assert len(list(result.scalars().all())) == 0