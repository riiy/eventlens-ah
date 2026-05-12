import pytest
from app.llm.mock_provider import MockLLMProvider


@pytest.mark.asyncio
async def test_extract_event_returns_valid_output():
    provider = MockLLMProvider()
    result = await provider.extract_event(
        title="贵州茅台宣布上调出厂价约20%",
        content="贵州茅台酒股份有限公司宣布自2024年1月1日起上调飞天茅台出厂价约20%，这是时隔6年后的首次提价。分析人士认为此举将显著提振茅台2024年业绩，利好白酒板块。",
        source="example_source",
        published_at="2024-01-01",
    )
    assert result.event_type in ("earnings_surprise", "other")
    assert result.market_scope in ("A_SHARE", "HK_SHARE", "BOTH", "UNKNOWN")
    assert 0 <= result.materiality_score <= 1
    assert 0 <= result.novelty_score <= 1
    assert result.event_summary  # non-empty


@pytest.mark.asyncio
async def test_extract_event_regulatory_keywords():
    provider = MockLLMProvider()
    result = await provider.extract_event(
        title="国家新闻出版署发布网络游戏管理办法",
        content="国家新闻出版署发布《网络游戏管理办法（草案征求意见稿）》，拟限制游戏内诱导性消费行为，禁止设置每日登录、首次充值等奖励机制。受此消息影响，腾讯、网易等游戏股大幅下跌。",
        source="example_source",
        published_at="2024-01-02",
    )
    assert result.event_type in ("regulatory_action", "policy_change")
    assert result.direction == "NEGATIVE"


@pytest.mark.asyncio
async def test_map_event_to_assets():
    provider = MockLLMProvider()
    assets = [
        {"symbol": "600519.SH", "name": "贵州茅台", "market": "A_SHARE", "sector": "Consumer Staples", "industry": "Liquor", "business_tags": ["白酒", "消费升级"]},
        {"symbol": "300750.SZ", "name": "宁德时代", "market": "A_SHARE", "sector": "Industrials", "industry": "Battery", "business_tags": ["新能源", "锂电池"]},
    ]
    result = await provider.map_event_to_assets(
        event_summary="贵州茅台提价20%，利好白酒板块",
        event_type="earnings_surprise",
        primary_entity="贵州茅台",
        assets=assets,
    )
    assert len(result.asset_links) >= 1
    for link in result.asset_links:
        assert 0 <= link.impact_strength <= 1
        assert 0 <= link.confidence_score <= 1
        assert link.symbol


@pytest.mark.asyncio
async def test_generate_hypothesis():
    provider = MockLLMProvider()
    result = await provider.generate_hypothesis(
        event_summary="贵州茅台提价20%，预计提振2024年业绩",
        event_type="earnings_surprise",
        linked_assets=[{"symbol": "600519.SH", "name": "贵州茅台", "market": "A_SHARE"}],
    )
    assert result.hypothesis_text
    assert len(result.supporting_evidence) > 0
    assert len(result.counter_evidence) > 0
    assert len(result.trigger_conditions) > 0
    assert len(result.invalidation_conditions) > 0
    assert result.time_horizon


@pytest.mark.asyncio
async def test_empty_assets_returns_empty():
    provider = MockLLMProvider()
    result = await provider.map_event_to_assets(
        event_summary="Some event",
        event_type="other",
        primary_entity="Unknown",
        assets=[],
    )
    assert result.asset_links == []