"""
Seed data for EventLens AH development and demo.

Upsert logic ensures idempotency -- safe to run multiple times.
"""

import hashlib
from datetime import datetime, timedelta
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Asset, RawDocument

# ---------------------------------------------------------------------------
# Seed Assets (10 equities covering A-share + HK markets)
# ---------------------------------------------------------------------------

SEED_ASSETS: list[dict] = [
    {
        "id": uuid4(),
        "symbol": "600519.SH",
        "name": "贵州茅台",
        "market": "A_SHARE",
        "exchange": "SSE",
        "sector": "Consumer Staples",
        "industry": "Liquor",
        "business_tags": ["白酒", "消费升级"],
        "metadata_json": {"is_demo_data": True},
    },
    {
        "id": uuid4(),
        "symbol": "000858.SZ",
        "name": "五粮液",
        "market": "A_SHARE",
        "exchange": "SZSE",
        "sector": "Consumer Staples",
        "industry": "Liquor",
        "business_tags": ["白酒", "消费升级"],
        "metadata_json": {"is_demo_data": True},
    },
    {
        "id": uuid4(),
        "symbol": "300750.SZ",
        "name": "宁德时代",
        "market": "A_SHARE",
        "exchange": "SZSE",
        "sector": "Industrials",
        "industry": "Battery",
        "business_tags": ["新能源", "锂电池", "电动车"],
        "metadata_json": {"is_demo_data": True},
    },
    {
        "id": uuid4(),
        "symbol": "601318.SH",
        "name": "中国平安",
        "market": "A_SHARE",
        "exchange": "SSE",
        "sector": "Financials",
        "industry": "Insurance",
        "business_tags": ["保险", "金融科技"],
        "metadata_json": {"is_demo_data": True},
    },
    {
        "id": uuid4(),
        "symbol": "000333.SZ",
        "name": "美的集团",
        "market": "A_SHARE",
        "exchange": "SZSE",
        "sector": "Consumer Discretionary",
        "industry": "Home Appliances",
        "business_tags": ["家电", "智能制造"],
        "metadata_json": {"is_demo_data": True},
    },
    {
        "id": uuid4(),
        "symbol": "002594.SZ",
        "name": "比亚迪",
        "market": "A_SHARE",
        "exchange": "SZSE",
        "sector": "Consumer Discretionary",
        "industry": "Automobiles",
        "business_tags": ["新能源车", "电池"],
        "metadata_json": {"is_demo_data": True},
    },
    {
        "id": uuid4(),
        "symbol": "0700.HK",
        "name": "腾讯控股",
        "market": "HK_SHARE",
        "exchange": "HKEX",
        "sector": "Technology",
        "industry": "Internet",
        "business_tags": ["互联网", "游戏", "云计算"],
        "metadata_json": {"is_demo_data": True},
    },
    {
        "id": uuid4(),
        "symbol": "9988.HK",
        "name": "阿里巴巴",
        "market": "HK_SHARE",
        "exchange": "HKEX",
        "sector": "Technology",
        "industry": "E-commerce",
        "business_tags": ["电商", "云计算", "AI"],
        "metadata_json": {"is_demo_data": True},
    },
    {
        "id": uuid4(),
        "symbol": "1810.HK",
        "name": "小米集团",
        "market": "HK_SHARE",
        "exchange": "HKEX",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "business_tags": ["智能手机", "IoT", "电动车"],
        "metadata_json": {"is_demo_data": True},
    },
    {
        "id": uuid4(),
        "symbol": "3690.HK",
        "name": "美团",
        "market": "HK_SHARE",
        "exchange": "HKEX",
        "sector": "Technology",
        "industry": "Local Services",
        "business_tags": ["外卖", "本地生活"],
        "metadata_json": {"is_demo_data": True},
    },
]

# ---------------------------------------------------------------------------
# Seed Documents -- realistic Chinese event-driven news snippets
# ---------------------------------------------------------------------------
now = datetime.utcnow()


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


SEED_DOCUMENTS: list[dict] = [
    {
        "id": uuid4(),
        "source": "证券时报",
        "source_type": "news",
        "url": "https://example.com/news/moutai-price-hike-2026",
        "title": "贵州茅台宣布上调飞天茅台出厂价20%",
        "content": (
            "贵州茅台酒股份有限公司今日发布公告，自2026年5月15日起，将53度飞天茅台酒"
            "出厂价由每瓶1499元上调至1799元，涨幅约20%。这是自2018年以来最大幅度的"
            "单次调价。公司表示，此次调价是基于市场供需关系变化及原材料成本上升等因素"
            "综合考虑后的决定。\n\n"
            "市场分析人士认为，茅台此次提价幅度超出市场普遍预期的10-15%，将直接提振"
            "公司2026年下半年营收和净利润。据测算，仅飞天茅台一项产品，提价后将增厚"
            "年利润约200亿元。白酒行业分析师张明表示，茅台提价具有行业风向标意义，"
            "可能带动高端白酒整体价格中枢上移。\n\n"
            "受此消息影响，白酒板块今日集体走强，多只白酒股涨幅超过5%。但部分投资者"
            "担心提价可能对终端销量产生一定抑制作用，后续需关注中秋节旺季动销数据。"
        ),
        "language": "zh",
        "published_at": now - timedelta(days=3),
        "crawled_at": now - timedelta(days=3, hours=-1),
        "credibility_score": 0.92,
        "metadata_json": {
            "is_demo_data": True,
            "event_type": "earnings_surprise",
            "market_scope": "A_SHARE",
            "direction": "POSITIVE",
        },
    },
    {
        "id": uuid4(),
        "source": "上海证券报",
        "source_type": "news",
        "url": "https://example.com/news/catl-solid-state-breakthrough",
        "title": "宁德时代发布全固态电池原型 能量密度突破500Wh/kg",
        "content": (
            "宁德时代新能源科技股份有限公司今日召开技术发布会，正式发布其新一代全固态"
            "电池原型产品。该产品采用公司自主研发的硫化物固态电解质技术路线，能量密度"
            "达到500Wh/kg，相比当前主流液态锂电池提升近一倍，同时通过最严苛的针刺"
            "安全测试。\n\n"
            "公司技术负责人透露，全固态电池预计2027年下半年实现小批量量产，初期将"
            "主要面向高端电动汽车和电动航空市场。量产成本目标为每度电800元以内，"
            "到2029年有望降至500元以下，接近当前液态锂电池成本。\n\n"
            "多家券商研报指出，全固态电池产业化进程加速将重塑锂电行业竞争格局，"
            "宁德时代在技术路线上的领先地位进一步巩固。不过也有分析师提醒，硫化物"
            "路线的量产工艺复杂度较高，实际产能爬坡速度仍需观察。"
        ),
        "language": "zh",
        "published_at": now - timedelta(days=7),
        "crawled_at": now - timedelta(days=7, hours=-2),
        "credibility_score": 0.95,
        "metadata_json": {
            "is_demo_data": True,
            "event_type": "product_launch",
            "market_scope": "A_SHARE",
            "direction": "POSITIVE",
        },
    },
    {
        "id": uuid4(),
        "source": "第一财经",
        "source_type": "news",
        "url": "https://example.com/news/tencent-gaming-regulation-draft",
        "title": "国家新闻出版署发布《网络游戏管理办法（征求意见稿）》 限制游戏内消费上限",
        "content": (
            "国家新闻出版署今日发布《网络游戏管理办法（征求意见稿）》，向社会公开征求"
            "意见。新规草案提出多项重要条款，包括：限制未成年人游戏充值金额上限为每月"
            "200元；要求所有游戏内虚拟道具抽取必须公示概率；禁止每日登录奖励等诱导性"
            "消费机制。\n\n"
            "腾讯控股作为国内最大的游戏公司，其游戏业务收入约占总营收的30%。分析人士"
            "指出，新规中关于限制游戏内消费的条款可能对腾讯《王者荣耀》《和平精英》等"
            "核心游戏的商业化模式产生实质性影响。花旗银行测算，在最严格的执行场景下，"
            "腾讯2026年游戏收入可能因此减少8-12%。\n\n"
            "腾讯方面回应称，将积极配合监管要求，同时强调公司游戏业务已形成多元化收入"
            "结构，海外游戏收入占比持续提升。征求意见稿反馈截止日期为2026年6月15日。"
        ),
        "language": "zh",
        "published_at": now - timedelta(days=5),
        "crawled_at": now - timedelta(days=5, hours=-1),
        "credibility_score": 0.90,
        "metadata_json": {
            "is_demo_data": True,
            "event_type": "regulatory_action",
            "market_scope": "HK_SHARE",
            "direction": "NEGATIVE",
        },
    },
    {
        "id": uuid4(),
        "source": "财联社",
        "source_type": "news",
        "url": "https://example.com/news/byd-eu-tariff-investigation",
        "title": "欧盟宣布对中国电动汽车启动反补贴调查 比亚迪或面临最高27%关税",
        "content": (
            "欧盟委员会今日正式宣布，将对中国出口至欧盟的电动汽车启动反补贴调查，"
            "调查范围涵盖比亚迪、上汽、吉利等多家中国车企。根据EU反补贴条例，调查"
            "期间最长为13个月，期间可能先征收临时反补贴关税。\n\n"
            "欧盟委员会在声明中表示，调查将重点关注中国政府对电动汽车产业链的补贴政策，"
            "包括电池原材料补贴、购置税减免、充电基础设施补贴等。初步估算显示，若认定"
            "补贴存在且造成损害，比亚迪可能面临15-27%的反补贴关税。\n\n"
            "比亚迪欧洲业务负责人回应称，公司在欧洲市场的定价策略基于正常商业决策，"
            "未因补贴获得不当竞争优势。目前比亚迪在欧洲新能源车市场份额约为8%，"
            "此次调查可能对其2027年欧洲扩张计划产生不利影响。但国内市场分析人士认为，"
            "比亚迪欧洲业务占比尚小（约3%），短期业绩影响有限。"
        ),
        "language": "zh",
        "published_at": now - timedelta(days=10),
        "crawled_at": now - timedelta(days=10, hours=-3),
        "credibility_score": 0.88,
        "metadata_json": {
            "is_demo_data": True,
            "event_type": "regulatory_action",
            "market_scope": "BOTH",
            "direction": "NEGATIVE",
        },
    },
    {
        "id": uuid4(),
        "source": "21世纪经济报道",
        "source_type": "news",
        "url": "https://example.com/news/pingan-property-exposure-report",
        "title": "中国平安地产敞口再引关注 旗下信托计划延期兑付规模逾300亿",
        "content": (
            "据21世纪经济报道援引知情人士消息，中国平安旗下平安信托管理的多只房地产"
            "信托计划出现延期兑付，涉及规模超过300亿元。消息人士称，相关计划底层资产"
            "主要为二三线城市商业地产项目和部分住宅项目，受房地产市场持续低迷影响，"
            "项目回款进度严重不及预期。\n\n"
            "中国平安方面回应表示，相关信托计划总体风险可控，公司已计提充足拨备。"
            "截至2026年一季度末，公司不动产投资占总资产比重已从2021年的约5.5%降至"
            "约3.2%，整体敞口持续收窄。\n\n"
            "不过，标普全球评级分析师指出，若房地产市场未能如预期般在2026年下半年"
            "企稳，平安可能需要进一步增加拨备，对全年利润构成压力。中国平安股价今日"
            "盘中一度下跌4.2%，创近两个月新低。多家券商维持'中性'评级。"
        ),
        "language": "zh",
        "published_at": now - timedelta(days=2),
        "crawled_at": now - timedelta(days=2, hours=-1),
        "credibility_score": 0.75,
        "metadata_json": {
            "is_demo_data": True,
            "event_type": "earnings_surprise",
            "market_scope": "A_SHARE",
            "direction": "NEGATIVE",
        },
    },
    {
        "id": uuid4(),
        "source": "科技日报",
        "source_type": "news",
        "url": "https://example.com/news/alibaba-cloud-ai-partnership",
        "title": "阿里云携手英伟达推出企业级AI推理一体机 中文模型性能较开源方案提升3倍",
        "content": (
            "阿里巴巴旗下阿里云今日在云栖大会上宣布，与英伟达联合推出新一代企业级AI"
            "推理一体机产品。该一体机搭载NVIDIA H200 GPU集群及阿里云自研的'通义'大模型"
            "优化引擎，在中文理解、法律文书、金融分析等场景下，模型推理性能较开源方案"
            "提升3倍，延迟降低60%。\n\n"
            "阿里云智能总裁表示，一体机产品面向金融机构、大型国企和安全敏感行业，"
            "主打私有化部署和全栈国产化适配。首批客户已包括三家头部券商和两家国有银行。"
            "定价方面，标准配置起售价为280万元/台，含三年软件订阅服务。\n\n"
            "分析师指出，阿里云此举精准切入信创和政企AI私有化部署这两大高增长赛道，"
            "有望成为阿里云业务新增长极。但同时，字节跳动、百度等竞争对手也在密集布局"
            "同类产品，市场竞争将在2026年下半年白热化。"
        ),
        "language": "zh",
        "published_at": now - timedelta(days=14),
        "crawled_at": now - timedelta(days=14, hours=-4),
        "credibility_score": 0.93,
        "metadata_json": {
            "is_demo_data": True,
            "event_type": "product_launch",
            "market_scope": "HK_SHARE",
            "direction": "POSITIVE",
        },
    },
    {
        "id": uuid4(),
        "source": "新浪财经",
        "source_type": "news",
        "url": "https://example.com/news/midea-kuka-robotics-acquisition",
        "title": "美的集团斥资42亿欧元收购德国工业机器人企业库卡剩余股权",
        "content": (
            "美的集团今日公告称，已与德国库卡集团剩余小股东达成协议，以42亿欧元"
            "（约合330亿元人民币）收购库卡集团剩余24.4%股权，完成后美的将全资控股库卡，"
            "并启动库卡从法兰克福证券交易所退市程序。\n\n"
            "美的集团董事长在公告中表示，全资控股库卡是集团'科技领先'战略的关键里程碑，"
            "将加速机器人与自动化技术在智能制造、智慧物流和医疗设备三大领域的应用落地。"
            "美的计划未来三年内向库卡追加投资20亿欧元，用于中国顺德和上海研发中心建设。\n\n"
            "产业分析人士认为，美的此举正值全球工业机器人需求回暖之际，全资控股后将"
            "大幅提升决策效率和技术整合深度。但42亿欧元的收购对价（对应库卡2025年EBITDA"
            "约18倍）估值偏高，市场对短期财务回报存有分歧。"
        ),
        "language": "zh",
        "published_at": now - timedelta(days=20),
        "crawled_at": now - timedelta(days=20, hours=-5),
        "credibility_score": 0.91,
        "metadata_json": {
            "is_demo_data": True,
            "event_type": "merger_acquisition",
            "market_scope": "A_SHARE",
            "direction": "MIXED",
        },
    },
    {
        "id": uuid4(),
        "source": "每日经济新闻",
        "source_type": "news",
        "url": "https://example.com/news/xiaomi-ev-delivery-100k",
        "title": "小米汽车SU7累计交付突破10万辆 提前完成全年目标",
        "content": (
            "小米集团今日通过官方微博宣布，旗下首款电动汽车SU7自2025年3月开启交付以来，"
            "累计交付量已正式突破10万辆，提前两个月完成2026年度交付目标。小米集团CEO"
            "雷军在社交媒体上表示，SU7在20-30万元纯电轿车细分市场中份额已达18%。\n\n"
            "交付数据显示，SU7月均交付量从初期的约5000辆攀升至近两个月的约12000辆，"
            "产能爬坡进度超出市场预期。小米北京亦庄工厂的二期产线已于上月投产，"
            "总规划年产能达到30万辆。此外，小米第二款车型SU7 Ultra（定价30-40万元区间）"
            "预订量已超过5万台。\n\n"
            "多家券商随后上调小米集团目标价，认为汽车业务有望在2026年第四季度实现盈亏"
            "平衡。但部分分析师依旧关注汽车业务的高资本开支对集团整体利润率的拖累，"
            "以及新能源车市场价格战加剧的风险。"
        ),
        "language": "zh",
        "published_at": now - timedelta(days=1),
        "crawled_at": now - timedelta(days=1, hours=-1),
        "credibility_score": 0.94,
        "metadata_json": {
            "is_demo_data": True,
            "event_type": "product_launch",
            "market_scope": "HK_SHARE",
            "direction": "POSITIVE",
        },
    },
]

# Populate content_hash for each document
for doc in SEED_DOCUMENTS:
    doc["content_hash"] = _hash_content(doc["content"])


# ---------------------------------------------------------------------------
# Upsert helpers
# ---------------------------------------------------------------------------

async def _upsert_assets(session: AsyncSession) -> int:
    """Insert or skip assets by symbol. Returns count of inserted rows."""
    inserted = 0
    for asset_data in SEED_ASSETS:
        result = await session.execute(
            sa.select(Asset).where(Asset.symbol == asset_data["symbol"])
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            session.add(Asset(**asset_data))
            inserted += 1
    if inserted:
        await session.flush()
    return inserted


async def _upsert_documents(session: AsyncSession) -> int:
    """Insert or skip documents by content_hash. Returns count of inserted rows."""
    inserted = 0
    for doc_data in SEED_DOCUMENTS:
        result = await session.execute(
            sa.select(RawDocument).where(RawDocument.content_hash == doc_data["content_hash"])
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            session.add(RawDocument(**doc_data))
            inserted += 1
    if inserted:
        await session.flush()
    return inserted


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

async def seed_database(session: AsyncSession) -> dict:
    """Idempotently seed the database with demo assets and documents.

    Returns a dict with counts of what was inserted.
    """
    assets_inserted = await _upsert_assets(session)
    docs_inserted = await _upsert_documents(session)
    await session.commit()

    return {
        "assets_inserted": assets_inserted,
        "assets_skipped": len(SEED_ASSETS) - assets_inserted,
        "documents_inserted": docs_inserted,
        "documents_skipped": len(SEED_DOCUMENTS) - docs_inserted,
        "total_assets": len(SEED_ASSETS),
        "total_documents": len(SEED_DOCUMENTS),
    }