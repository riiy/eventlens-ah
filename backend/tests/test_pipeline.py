import pytest
from uuid import uuid4

from app.models.asset import Asset
from app.models.event_asset_link import EventAssetLink
from app.models.llm_run_log import LLMRunLog
from app.models.market_event import MarketEvent
from app.models.raw_document import RawDocument
from app.services.event_service import EventService
from app.services.hypothesis_service import HypothesisService
from sqlalchemy import select, func


@pytest.mark.asyncio
async def test_full_pipeline_happy_path(async_session):
    """Create a document, run all 7 pipeline steps, verify integrity."""
    service = EventService()
    hypo_service = HypothesisService()

    # Step 1: 信息入库
    doc = RawDocument(
        source="证券时报",
        source_type="news",
        title="宁德时代发布全固态电池 能量密度突破500Wh/kg",
        content="宁德时代今日发布全固态电池原型，能量密度达到500Wh/kg，计划2025年量产。消息发布后，公司股价上涨5%。分析人士认为这将重塑动力电池行业竞争格局。",
        language="zh",
        credibility_score=0.92,
    )
    async_session.add(doc)
    await async_session.flush()

    # Step 2: 事件抽取
    event = await service.extract_from_document(async_session, doc.id)
    assert event is not None
    assert event.raw_document_id == doc.id
    assert event.status == "EXTRACTED"

    # Verify LLMRunLog for extraction
    extract_logs = (await async_session.execute(
        select(LLMRunLog).where(LLMRunLog.task_type == "extract_event")
    )).scalars().all()
    assert len(extract_logs) >= 1

    # Step 3: 标的映射 — need assets first
    asset = Asset(
        symbol="300750.SZ", name="宁德时代", market="A_SHARE", exchange="SZSE",
    )
    async_session.add(asset)
    await async_session.flush()

    links = await service.map_assets(async_session, event.id)
    assert len(links) >= 1
    assert links[0].asset_id == asset.id

    # Step 4+5: 假设生成 (includes 风险反证)
    hypothesis = await service.generate_hypothesis(async_session, event.id)
    assert hypothesis is not None
    assert hypothesis.event_id == event.id
    assert hypothesis.hypothesis_text
    assert hypothesis.impact_chain
    assert len(hypothesis.supporting_evidence) > 0
    assert len(hypothesis.counter_evidence) > 0  # 风险反证
    assert len(hypothesis.trigger_conditions) > 0
    assert len(hypothesis.invalidation_conditions) > 0
    assert hypothesis.status == "ACTIVE"

    # Step 6: 打分排序
    scored = await service.score(async_session, event.id)
    assert scored is not None
    assert scored.event_alpha_score > 0
    assert scored.status == "SCORED"

    # Step 7: 后续表现记录
    reactions = await hypo_service.generate_mock_price_reactions(async_session, event.id)
    assert len(reactions) >= 1
    assert reactions[0].return_1d is not None
    assert reactions[0].asset_id == asset.id

    # Verify LLMRunLogs: should have extract + map + hypothesis = 3
    total_logs = (await async_session.execute(
        select(func.count()).select_from(LLMRunLog)
    )).scalar()
    assert total_logs >= 3, f"Expected >=3 LLMRunLogs, got {total_logs}"


@pytest.mark.asyncio
async def test_pipeline_handles_no_assets(async_session):
    """When no assets exist, map_assets returns empty, generate_hypothesis returns None."""
    service = EventService()

    doc = RawDocument(
        source="test", title="Test", content="Test content for extraction.",
        language="zh",
    )
    async_session.add(doc)
    await async_session.flush()

    event = await service.extract_from_document(async_session, doc.id)
    assert event is not None

    # map_assets with zero assets in DB
    links = await service.map_assets(async_session, event.id)
    assert links == []

    # generate_hypothesis with no linked assets
    hypothesis = await service.generate_hypothesis(async_session, event.id)
    assert hypothesis is None


@pytest.mark.asyncio
async def test_pipeline_handles_invalid_document(async_session):
    """Extracting from non-existent document returns None gracefully."""
    service = EventService()
    result = await service.extract_from_document(async_session, uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_llm_run_logs_span_all_tasks(async_session):
    """After running full pipeline, all three task types are represented in logs."""
    service = EventService()
    hypo_service = HypothesisService()

    doc = RawDocument(
        source="test", title="茅台提价",
        content="贵州茅台宣布上调出厂价20%，利好白酒板块。",
        language="zh",
    )
    async_session.add(doc)
    await async_session.flush()

    asset = Asset(
        symbol="600519.SH", name="贵州茅台", market="A_SHARE", exchange="SSE",
    )
    async_session.add(asset)
    await async_session.flush()

    event = await service.extract_from_document(async_session, doc.id)
    await service.map_assets(async_session, event.id)
    await service.generate_hypothesis(async_session, event.id)
    await hypo_service.generate_mock_price_reactions(async_session, event.id)
    await service.score(async_session, event.id)

    result = await async_session.execute(
        select(LLMRunLog.task_type, func.count()).group_by(LLMRunLog.task_type)
    )
    task_counts = dict(result.all())
    assert "extract_event" in task_counts
    assert "map_assets" in task_counts
    assert "generate_hypothesis" in task_counts