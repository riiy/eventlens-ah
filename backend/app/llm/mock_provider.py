import asyncio
import logging
import random
import re

from app.llm.base import BaseLLMProvider
from app.schemas.llm_outputs import (
    AssetLinkOutput,
    AssetMappingOutput,
    ExtractedEventOutput,
    HypothesisOutput,
)

logger = logging.getLogger(__name__)


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider using keyword matching. Works without any API keys."""

    def __init__(self, model_name: str = "mock") -> None:
        super().__init__(model_name)

    # ------------------------------------------------------------------
    # event_type detection helpers
    # ------------------------------------------------------------------
    _EVENT_PATTERNS: list[tuple[list[str], str]] = [
        (["涨价", "提价", "出厂价", "上调价格", "价格上调"], "earnings_surprise"),
        (["监管", "处罚", "调查", "立案", "办法", "警示函", "约谈", "整改"], "regulatory_action"),
        (["收购", "并购", "整合", "重组", "控股"], "merger_acquisition"),
        (["政策", "国务院", "发改委", "工信部", "央行", "银保监", "证监会"], "policy_change"),
        (["发布", "推出", "上市", "新品", "首发", "发布新品", "新产品"], "product_launch"),
        (["制裁", "关税", "地缘", "冲突", "中美", "台海", "南海"], "geopolitical"),
        (["供应链", "产能", "停产", "断供", "缺芯"], "industry_disruption"),
        (["辞职", "换帅", "CEO", "董事长", "高管变更", "人事变动"], "management_change"),
        (["涨停", "跌停", "异动", "成交量", "龙虎榜"], "market_anomaly"),
    ]

    _SCOPE_PATTERNS: list[tuple[list[str], str]] = [
        (["A股", "沪深", "上证", "深证", "科创板", "创业板"], "A_SHARE"),
        (["港股", "恒生", "H股", "港交所"], "HK_SHARE"),
        (["A股", "港股", "沪深港通"], "BOTH"),
    ]

    _DIRECTION_PATTERNS: list[tuple[list[str], str]] = [
        (["利好", "增长", "提升", "上涨", "盈利", "突破", "积极", "支持"], "POSITIVE"),
        (["利空", "下降", "下跌", "亏损", "风险", "处罚", "制裁", "调查"], "NEGATIVE"),
    ]

    # ------------------------------------------------------------------
    # extract_event
    # ------------------------------------------------------------------
    async def extract_event(
        self, title: str, content: str, source: str, published_at: str
    ) -> ExtractedEventOutput:
        full_text = f"{title}\n{content}"
        await asyncio.sleep(0.05)

        event_type = self._detect_event_type(full_text)
        primary_entity = self._extract_primary_entity(full_text)
        related_entities = self._extract_related_entities(full_text, primary_entity)
        market_scope = self._detect_scope(full_text)
        direction = self._detect_direction(full_text, event_type)

        scores = self._score_event(event_type, direction)

        reasoning_summary = self._build_reasoning(
            event_type, primary_entity, direction, full_text
        )

        return ExtractedEventOutput(
            event_type=event_type,
            event_summary=self._summarize(title, full_text, event_type),
            primary_entity=primary_entity,
            related_entities=related_entities,
            market_scope=market_scope,
            direction=direction,
            materiality_score=scores["materiality"],
            novelty_score=scores["novelty"],
            urgency_score=scores["urgency"],
            confidence_score=scores["confidence"],
            risk_score=scores["risk"],
            reasoning_summary=reasoning_summary,
            risk_flags=["数据基于公开信息", "需进一步验证", "模型自动分析结果仅供参考"],
        )

    def _detect_event_type(self, text: str) -> str:
        for keywords, etype in self._EVENT_PATTERNS:
            for kw in keywords:
                if kw in text:
                    return etype
        return "other"

    def _detect_scope(self, text: str) -> str:
        matched = []
        for keywords, scope in self._SCOPE_PATTERNS:
            for kw in keywords:
                if kw in text:
                    matched.append(scope)
                    break
        if "BOTH" in matched:
            return "BOTH"
        if len(set(matched)) >= 2:
            return "BOTH"
        if matched:
            return matched[0]
        return "A_SHARE"

    def _detect_direction(self, text: str, event_type: str) -> str:
        positive_hits = 0
        negative_hits = 0
        for keywords, direction in self._DIRECTION_PATTERNS:
            for kw in keywords:
                if kw in text:
                    if direction == "POSITIVE":
                        positive_hits += 1
                    else:
                        negative_hits += 1
        # Certain event types bias direction
        if event_type == "regulatory_action":
            negative_hits += 1
        elif event_type == "product_launch":
            positive_hits += 1
        elif event_type == "earnings_surprise" and "涨价" in text:
            positive_hits += 1

        if positive_hits > negative_hits:
            return "POSITIVE"
        if negative_hits > positive_hits:
            return "NEGATIVE"
        if positive_hits == 0 and negative_hits == 0:
            return "NEUTRAL"
        return "MIXED"

    _STOCK_RE = re.compile(r"(\d{6})\.(SH|SZ|HK)")

    def _extract_primary_entity(self, text: str) -> str:
        # Try to find stock symbol
        match = self._STOCK_RE.search(text)
        if match:
            return f"{match.group(1)}.{match.group(2)}"

        # Bag of common company name suffixes for Chinese companies
        company_re = re.compile(
            r"([一-鿿]{2,12}(?:股份|集团|科技|医药|电子|新能源|半导体|"
            r"银行|保险|证券|基金|地产|汽车|能源|通信|互联网|软件|硬件|传媒|"
            r"食品|饮料|制药|生物|化学|材料|设备|制造|光电|电气|芯片|光伏|"
            r"锂电|储能|军工|航空|船舶|钢铁|煤炭|有色|石油|化工|建材|"
            r"有限公司|有限责任公司|公司))"
        )
        match = company_re.search(text)
        if match:
            return match.group(1)
        return "未识别主体"

    def _extract_related_entities(
        self, text: str, primary: str
    ) -> list[str]:
        symbols = self._STOCK_RE.findall(text)
        entities = [f"{num}.{mkt}" for num, mkt in symbols if f"{num}.{mkt}" != primary]
        # Add generic industry references
        industry_refs = re.findall(r"([一-鿿]{2,6}(?:行业|板块|概念))", text)
        entities.extend(industry_refs[:3])
        return list(dict.fromkeys(entities))[:5]  # dedupe, max 5

    def _score_event(
        self, event_type: str, direction: str
    ) -> dict[str, float]:
        r = random.Random()
        jitter = lambda: r.uniform(-0.06, 0.06)

        base = {
            "earnings_surprise": (0.78, 0.70, 0.82, 0.75, 0.30),
            "product_launch": (0.65, 0.88, 0.60, 0.72, 0.25),
            "merger_acquisition": (0.85, 0.82, 0.68, 0.78, 0.35),
            "regulatory_action": (0.82, 0.72, 0.85, 0.80, 0.72),
            "policy_change": (0.90, 0.55, 0.70, 0.78, 0.50),
            "geopolitical": (0.72, 0.80, 0.75, 0.68, 0.85),
            "industry_disruption": (0.70, 0.78, 0.72, 0.70, 0.60),
            "management_change": (0.55, 0.68, 0.50, 0.65, 0.35),
            "market_anomaly": (0.60, 0.85, 0.88, 0.62, 0.55),
            "other": (0.50, 0.60, 0.55, 0.60, 0.40),
        }

        m, n, u, c, risk = base.get(event_type, base["other"])

        def clamp(v: float) -> float:
            return round(max(0.0, min(1.0, v)), 4)

        # Apply negative bias for negative direction
        neg_bias = 0.08 if direction in ("NEGATIVE", "MIXED") else 0.0

        return {
            "materiality": clamp(m + jitter()),
            "novelty": clamp(n + jitter()),
            "urgency": clamp(u + jitter()),
            "confidence": clamp(c + jitter()),
            "risk": clamp(risk + jitter() + neg_bias),
        }

    def _summarize(self, title: str, text: str, event_type: str) -> str:
        type_label = {
            "earnings_surprise": "业绩变动",
            "product_launch": "产品发布",
            "merger_acquisition": "并购重组",
            "regulatory_action": "监管行动",
            "policy_change": "政策变动",
            "geopolitical": "地缘政治",
            "industry_disruption": "行业扰动",
            "management_change": "管理层变动",
            "market_anomaly": "市场异动",
            "other": "其他事件",
        }.get(event_type, "市场事件")

        # Truncate to create a realistic summary
        snippet = text[:120].replace("\n", " ")
        return f"[{type_label}] {title}：{snippet}..."

    def _build_reasoning(
        self, text: str, entity: str, direction: str, full_text: str
    ) -> str:
        direction_cn = {"POSITIVE": "正面", "NEGATIVE": "负面", "NEUTRAL": "中性", "MIXED": "混合"}.get(
            direction, "未知"
        )
        templates = [
            f"基于对事件标题和内容的关键词分析，识别到主要实体为{entity}，事件影响方向为{direction_cn}。"
            f"结合事件类型特征和历史数据模式，给出了各维度的评估分数。",
            f"通过自然语言处理技术对文本进行语义分析，确定{entity}为核心实体，整体影响呈{direction_cn}。"
            f"根据事件类型匹配了相应的评分模型，生成了多维度评估结果。",
            f"经分析，该事件涉及{entity}，从文本信号来看影响偏{direction_cn}。"
            f"基于市场类似事件的统计特征，推算了各评分维度数值。",
            f"系统提取到核心实体{entity}，文本情绪分析表明事件具有{direction_cn}影响。"
            f"利用事件分类器和评分模型完成了自动化评估。",
            f"分析引擎识别到关键实体{entity}，事件信号指向{direction_cn}方向。"
            f"综合考虑事件类型、实体特征和市场环境，生成了多维度评分。",
        ]
        return random.choice(templates)

    # ------------------------------------------------------------------
    # map_event_to_assets
    # ------------------------------------------------------------------
    async def map_event_to_assets(
        self,
        event_summary: str,
        event_type: str,
        primary_entity: str,
        assets: list[dict],
    ) -> AssetMappingOutput:
        await asyncio.sleep(0.05)

        if not assets:
            return AssetMappingOutput(asset_links=[])

        combined_text = f"{event_summary} {primary_entity}"
        links: list[AssetLinkOutput] = []

        # Score each asset by relevance and pick top 1-3
        scored: list[tuple[float, dict]] = []
        for asset in assets:
            score = self._asset_match_score(combined_text, event_type, asset)
            if score > 0.15:
                scored.append((score, asset))

        scored.sort(key=lambda x: x[0], reverse=True)
        selected = scored[: random.randint(1, min(3, len(scored)))]

        direction = self._detect_direction(combined_text, event_type)

        for score_val, asset in selected:
            link = self._build_asset_link(asset, direction, event_type, score_val)
            links.append(link)

        return AssetMappingOutput(asset_links=links)

    def _asset_match_score(
        self, text: str, event_type: str, asset: dict
    ) -> float:
        r = random.Random()
        score = 0.0
        name = asset.get("name", "")
        symbol = asset.get("symbol", "")
        tags = asset.get("business_tags", [])
        if isinstance(tags, str):
            tags = [tags]

        # Check name match
        for char in name[:4]:
            if char in text:
                score += 0.15

        # Check symbol match
        if symbol and symbol in text:
            score += 0.30

        # Check tag match
        for tag in tags:
            if tag in text:
                score += 0.20

        # Base relevance
        score += 0.10

        # Add some controlled randomness for variety
        score += r.uniform(0.0, 0.10)

        return min(score, 1.0)

    def _build_asset_link(
        self, asset: dict, direction: str, event_type: str, match_score: float
    ) -> AssetLinkOutput:
        name = asset.get("name", "未知资产")
        symbol = asset.get("symbol", "000000.SH")
        market = asset.get("market", "SH")

        # Determine impact direction
        impact = direction if direction in ("POSITIVE", "NEGATIVE") else "NEUTRAL"
        # Some event types flip the direction for certain asset classes
        if event_type == "regulatory_action" and impact == "POSITIVE":
            impact = "NEUTRAL"

        strength = round(max(0.2, min(1.0, match_score + random.uniform(-0.1, 0.1))), 4)
        confidence = round(max(0.3, match_score * 0.9 + random.uniform(0.0, 0.1)), 4)

        reasons = [
            f"{name}（{symbol}）为{event_type}事件的直接关联标的，与事件核心实体存在业务协同关系，预计将受到{impact}影响。",
            f"基于行业分析和供应链关系，{name}与事件描述中的关键主体高度相关，事件对其经营环境产生{impact}影响。",
            f"{name}所处行业与事件类型匹配度高，历史类似事件中该标的通常表现出{impact}反应。",
            f"通过业务标签匹配，{name}的核心业务与事件驱动因素高度重合，影响方向预计为{impact}。",
            f"综合分析{name}的业务构成与市场定位，该事件对其营收和估值将产生{impact}影响，建议关注。",
        ]

        return AssetLinkOutput(
            symbol=symbol,
            name=name,
            market=market,
            impact_direction=impact,
            impact_strength=strength,
            reason=random.choice(reasons).replace("{impact}", impact),
            confidence_score=confidence,
        )

    # ------------------------------------------------------------------
    # generate_hypothesis
    # ------------------------------------------------------------------
    async def generate_hypothesis(
        self,
        event_summary: str,
        event_type: str,
        linked_assets: list[dict],
    ) -> HypothesisOutput:
        await asyncio.sleep(0.05)

        templates = self._get_hypothesis_templates(event_type)
        template = random.choice(templates)

        asset_names = [a.get("name", "相关资产") for a in linked_assets[:3]]
        assets_str = "、".join(asset_names) if asset_names else "相关标的"

        direction = "正面" if random.random() > 0.3 else "负面"
        if event_type in ("regulatory_action", "geopolitical"):
            direction = "负面"

        hypothesis_text = template["hypothesis"].format(assets=assets_str, direction=direction)
        impact_chain = [step.strip() for step in template["impact_chain"].format(assets=assets_str).split("->")]

        return HypothesisOutput(
            hypothesis_text=hypothesis_text,
            impact_chain=impact_chain,
            supporting_evidence=[
                e.format(assets=assets_str) for e in template["supporting"]
            ],
            counter_evidence=[
                e.format(assets=assets_str) for e in template["counter"]
            ],
            trigger_conditions=[
                t.format(assets=assets_str) for t in template["triggers"]
            ],
            invalidation_conditions=[
                i.format(assets=assets_str) for i in template["invalidations"]
            ],
            time_horizon=template["horizon"],
            risk_notes=template["risk_notes"],
        )

    _HYPOTHESIS_TEMPLATES: dict[str, list[dict]] = {
        "earnings_surprise": [
            {
                "hypothesis": "{assets}将因业绩超预期获得估值修复，短期内股价有望{direction}波动，幅度预计在5-15%区间。",
                "impact_chain": "业绩公告 -> 分析师上调盈利预测 -> 机构增持 -> {assets}股价上行 -> 同行业估值联动",
                "supporting": [
                    "同行业可比公司近期业绩普遍向好，行业景气度上行",
                    "{assets}成本控制能力增强，毛利率连续三个季度改善",
                    "北向资金近期持续净流入该板块，外资看好",
                    "公司产能利用率提升至历史高位，量价齐升逻辑成立",
                ],
                "counter": [
                    "需警惕业绩基数效应导致的增长幻觉",
                    "行业竞争加剧可能侵蚀超额利润",
                ],
                "triggers": [
                    "下一季度财报继续超预期",
                    "大股东或高管增持公告",
                    "券商密集上调目标价",
                ],
                "invalidations": [
                    "下游需求意外萎缩",
                    "原材料成本大幅上升侵蚀利润",
                ],
                "horizon": "SHORT_TERM",
                "risk_notes": "业绩超预期可能是非经常性损益驱动，须拆解利润来源。短期股价可能已部分PRICE IN，追高需谨慎。数据仅基于公开信息，不构成投资建议。",
            },
            {
                "hypothesis": "提价逻辑驱动{assets}盈利能力改善，全年业绩有望上调，中期配置价值凸显。",
                "impact_chain": "产品提价 -> 毛利率提升 -> 盈利预测上修 -> {assets}估值中枢抬升 -> 资金持续流入",
                "supporting": [
                    "公司产品具有较强品牌溢价，提价后销量下滑风险可控",
                    "成本端原材料价格回落，利润弹性加大",
                    "机构调研频次增加，关注度持续提升",
                    "历史提价周期中股价平均涨幅20%+",
                ],
                "counter": [
                    "终端消费疲软可能导致提价效果打折扣",
                    "竞品未跟进提价，市场份额存在流失风险",
                ],
                "triggers": [
                    "公司发布正式调价函",
                    "月度经营数据验证提价传导顺畅",
                    "卖方发布深度报告上调目标价",
                ],
                "invalidations": [
                    "提价后出货量大幅下降",
                    "竞品降价抢夺市场份额",
                ],
                "horizon": "MEDIUM_TERM",
                "risk_notes": "提价效应需2-3个季度才能在报表充分体现，短期股价博弈情绪较重。消费环境变化可能影响提价传导效果。",
            },
            {
                "hypothesis": "{assets}业绩拐点已现，周期反转逻辑成立，建议在回调中逐步布局。",
                "impact_chain": "行业底部确认 -> 龙头企业率先复苏 -> {assets}订单回暖 -> 估值修复 -> 盈利兑现",
                "supporting": [
                    "行业库存周期见底，补库需求逐步释放",
                    "公司PB估值处于历史10%分位以下，安全边际充足",
                    "产业链调研显示订单可见度改善",
                    "政策端持续释放稳增长信号",
                ],
                "counter": [
                    "需求复苏斜率可能不及预期",
                    "产能出清不彻底或延后反转时点",
                ],
                "triggers": [
                    "月度PMI/行业数据验证复苏趋势",
                    "公司预告业绩大幅改善",
                    "产业资本或大股东增持",
                ],
                "invalidations": [
                    "宏观经济大幅下行",
                    "行业二次探底",
                ],
                "horizon": "MEDIUM_TERM",
                "risk_notes": "周期反转判断具有较大不确定性，左侧布局需控制仓位和耐心。建议等待右侧确认信号再加仓。",
            },
            {
                "hypothesis": "{assets}受益于成本改善，业绩弹性释放，具备波段交易机会。",
                "impact_chain": "原材料降价 -> 生产成本下行 -> 毛利率扩张 -> {assets}季度利润大增 -> 股价反弹",
                "supporting": [
                    "主要原材料价格同比降幅超过20%",
                    "公司产品定价相对刚性，成本下降直接转化为利润",
                    "同板块成本敏感型公司已率先反应",
                ],
                "counter": [
                    "成本下降可能伴随需求走弱，量减抵消价增",
                    "公司可能通过降价让利下游，利润转化不充分",
                ],
                "triggers": [
                    "下一季报毛利率明显提升",
                    "原材料价格继续下行",
                ],
                "invalidations": [
                    "原材料价格反弹",
                    "下游客户要求降价分成",
                ],
                "horizon": "SHORT_TERM",
                "risk_notes": "成本驱动的利润弹性持续性存疑，一旦原材料价格反弹逻辑即刻逆转。适合短线操作。",
            },
        ],
        "policy_change": [
            {
                "hypothesis": "新一轮产业政策利好{assets}，板块将迎来主题性投资机会，建议积极参与。",
                "impact_chain": "政策文件发布 -> 市场预期形成 -> {assets}估值提升 -> 增量资金入市 -> 行情扩散",
                "supporting": [
                    "政策层级高（国务院/发改委），执行力度有保障",
                    "历史类似政策发布后板块平均涨幅25%以上",
                    "当前{assets}估值处于合理区间，具备向上空间",
                    "配套财政和金融政策有望陆续出台形成合力",
                ],
                "counter": [
                    "政策从出台到落地存在时滞，实际效果待验证",
                    "市场可能已部分消化政策预期",
                ],
                "triggers": [
                    "细则文件正式印发",
                    "试点城市或项目名单公布",
                    "配套资金拨付到位",
                ],
                "invalidations": [
                    "政策执行力度低于预期",
                    "宏观经济环境突变导致政策优先级调整",
                ],
                "horizon": "MEDIUM_TERM",
                "risk_notes": "政策主题投资具有事件驱动特征，需注意节奏把握。政策效果需长期跟踪，短期炒作后可能回调。研究基于公开政策文件，不构成投资建议。",
            },
            {
                "hypothesis": "政策红利驱动{assets}进入新一轮增长周期，中长期配置价值突出，建议超配。",
                "impact_chain": "顶层设计定调 -> 产业规划落地 -> 需求爆发 -> {assets}收入加速 -> 戴维斯双击",
                "supporting": [
                    "写入五年规划/政府工作报告，政策优先级最高",
                    "国际比较显示国内渗透率提升空间大",
                    "产业链上下游配套日渐成熟，形成正向循环",
                    "地方政府积极响应，招商引资力度加大",
                ],
                "counter": [
                    "技术路线存在不确定性，可能出现替代方案",
                    "产能扩张过快可能导致阶段性过剩",
                ],
                "triggers": [
                    "重大示范项目开标或投产",
                    "行业技术标准正式发布",
                    "关键成本突破使商业模式跑通",
                ],
                "invalidations": [
                    "技术路线被颠覆",
                    "国际环境变化导致供应链受阻",
                ],
                "horizon": "LONG_TERM",
                "risk_notes": "长期逻辑确定性较高但过程波动较大，适合在调整时分批建仓。政策节奏和力度变化需持续跟踪。",
            },
            {
                "hypothesis": "产业打压政策下{assets}承压，短期回避为主，等待政策底确认后再评估。",
                "impact_chain": "监管收紧 -> 行业增速放缓 -> {assets}盈利预期下修 -> 估值中枢下行 -> 资金流出",
                "supporting": [
                    "政策口径明显转向收紧，监管态度坚决",
                    "同行业海外市场被限制的案例可供参考",
                    "机构持仓集中度较高，多杀多风险存在",
                ],
                "counter": [
                    "政策冲击被市场过度反应，估值已超跌",
                    "龙头企业抗风险能力强于中小公司",
                ],
                "triggers": [
                    "正式监管文件出台",
                    "主要公司下调业绩指引",
                    "大股东减持公告",
                ],
                "invalidations": [
                    "政策落地力度温和",
                    "行业自律取得成效监管回摆",
                ],
                "horizon": "SHORT_TERM",
                "risk_notes": "监管风险是最难定价的风险类型之一，建议右侧交易。政策冲击下流动性可能骤降，注意仓位管理。",
            },
            {
                "hypothesis": "货币政策转向利好{assets}流动性环境改善，短期反弹可期但持续性待观察。",
                "impact_chain": "降准/降息 -> 流动性宽松 -> 无风险利率下行 -> {assets}估值修复 -> 风险偏好回升",
                "supporting": [
                    "央行操作节奏和力度超预期，释放明确宽松信号",
                    "利率敏感型板块已率先反应，{assets}有望跟随",
                    "海外货币政策同步宽松形成共振",
                ],
                "counter": [
                    "宽松已被市场充分预期，利好兑现即利空",
                    "流动性向实体传导不畅，资产价格受益有限",
                ],
                "triggers": [
                    "LPR/MLF利率下调",
                    "社融数据超预期",
                    "北向资金大幅净流入",
                ],
                "invalidations": [
                    "通胀数据超预期制约宽松空间",
                    "汇率贬值压力迫使政策收紧",
                ],
                "horizon": "SHORT_TERM",
                "risk_notes": "货币政策对股市的影响链条长且复杂，流动性驱动行情波动大。需关注通胀和汇率约束。",
            },
        ],
        "merger_acquisition": [
            {
                "hypothesis": "并购整合将产生显著协同效应，{assets}价值重估在即，建议关注套利机会。",
                "impact_chain": "并购公告 -> 市场重估整合价值 -> {assets}股价向要约价收敛 -> 套利空间缩小 -> 整合落地验证",
                "supporting": [
                    "并购标的与收购方业务高度互补，协同效应明确",
                    "交易估值合理，未出现溢价过高的情况",
                    "大股东承诺参与，交易确定性较高",
                    "监管部门审批通过概率大",
                ],
                "counter": [
                    "整合执行风险不可忽视，历史成功率约50%",
                    "换股收购可能导致原股东权益稀释",
                ],
                "triggers": [
                    "反垄断审查无条件通过",
                    "股东大会高票批准",
                    "整合方案细节披露超预期",
                ],
                "invalidations": [
                    "监管否决或附加苛刻条件",
                    "竞购方出现引发价格战",
                ],
                "horizon": "MEDIUM_TERM",
                "risk_notes": "并购套利需关注审批风险和时间成本，现金收购和换股收购风险特征不同。整合效果需3-5年验证。",
            },
            {
                "hypothesis": "行业整合加速，{assets}作为龙头受益于集中度提升，市场份额和议价能力双升。",
                "impact_chain": "并购落地 -> 竞争格局优化 -> {assets}市占率提升 -> 定价权增强 -> 盈利超预期",
                "supporting": [
                    "行业CR3集中度将提升至70%以上，竞争趋缓",
                    "采购和研发协同降低成本，规模效应显现",
                    "行业低效产能出清，龙头议价能力增强",
                ],
                "counter": [
                    "反垄断风险，监管可能关注过高集中度",
                    "整合期管理精力分散影响主业",
                ],
                "triggers": [
                    "整合完成后首份财报超预期",
                    "市场份额数据验证集中度提升",
                    "新任管理团队释放整合顺利信号",
                ],
                "invalidations": [
                    "整合不顺核心人才流失",
                    "竞争对手借机抢夺客户",
                ],
                "horizon": "LONG_TERM",
                "risk_notes": "行业整合是大趋势但过程曲折，短期内面临整合阵痛。建议关注整合关键节点的经营数据。",
            },
            {
                "hypothesis": "并购标的质地优良，{assets}通过此次收购打开第二增长曲线，成长空间大幅拓宽。",
                "impact_chain": "跨界收购 -> 进入新市场 -> {assets}业务多元化 -> 估值体系切换 -> 长期市值增长",
                "supporting": [
                    "标的公司处于高景气赛道，行业增速30%+",
                    "收购方具备赋能能力（渠道/技术/资金）",
                    "对标海外同业，多元业务公司享有估值溢价",
                ],
                "counter": [
                    "跨界整合难度大，文化冲突是常见陷阱",
                    "管理层精力分散可能拖累原有业务",
                ],
                "triggers": [
                    "新业务首单落地或大客户签约",
                    "协同项目取得阶段性成果",
                ],
                "invalidations": [
                    "新业务进展严重低于预期",
                    "商誉减值风险暴露",
                ],
                "horizon": "LONG_TERM",
                "risk_notes": "跨界收购风险高于同业整合，商誉减值是最常见的地雷。建议密切跟踪新业务独立经营数据。",
            },
        ],
        "regulatory_action": [
            {
                "hypothesis": "监管处罚对{assets}短期冲击明显，但中长期不改变公司基本面，超跌后或有布局机会。",
                "impact_chain": "处罚公告 -> 恐慌性抛售 -> {assets}超跌 -> 市场消化利空 -> 基本面驱动的修复",
                "supporting": [
                    "历史类似处罚案例中，公司在6个月内平均反弹15%",
                    "处罚金额相对公司利润规模有限，非毁灭性打击",
                    "公司业务护城河深厚，客户粘性高",
                ],
                "counter": [
                    "连续处罚可能引发连锁反应（大客户解约/银行抽贷）",
                    "声誉损失难以量化但可能持久影响业务",
                ],
                "triggers": [
                    "公司整改方案公布",
                    "业务数据验证影响可控",
                    "机构资金逢低入场",
                ],
                "invalidations": [
                    "发现新的违规问题",
                    "处罚升级为业务暂停或牌照吊销",
                ],
                "horizon": "SHORT_TERM",
                "risk_notes": "监管处罚的不确定性高，建议等待事件充分消化后再评估。如果涉及业务资质受影响则是性质变化。",
            },
            {
                "hypothesis": "监管趋严背景下，不合规的{assets}面临出清风险，行业龙头合规优势凸显，建议向头部集中。",
                "impact_chain": "监管新规 -> 中小公司退出 -> {assets}（龙头）承接市场份额 -> 行业集中度提升 -> 龙头溢价",
                "supporting": [
                    "行业合规成本大幅上升，中小企业难以承受",
                    "龙头企业已提前布局合规体系，成本影响可控",
                    "海外市场类似监管周期中龙头超额收益显著",
                ],
                "counter": [
                    "合规成本最终转嫁为全社会成本，行业增速放缓",
                    "监管不确定性本身压制板块估值",
                ],
                "triggers": [
                    "中小竞争对手宣布退出",
                    "行业准入门槛正式提高",
                ],
                "invalidations": [
                    "监管政策出现重大调整或松绑",
                    "新技术路线绕开监管壁垒",
                ],
                "horizon": "MEDIUM_TERM",
                "risk_notes": "监管是双刃剑，既是龙头护城河也可能变成创新枷锁。需持续跟踪政策动态和行业边际变化。",
            },
        ],
        "product_launch": [
            {
                "hypothesis": "重磅新品打开{assets}成长空间，产品周期驱动业绩加速，建议在量产爬坡阶段布局。",
                "impact_chain": "新品发布 -> 预订/订单数据验证需求 -> {assets}产能爬坡 -> 收入增量兑现 -> 估值切换",
                "supporting": [
                    "新品性能/价格相比竞品有明显优势",
                    "市场空间测算显示增量收入可达当前营收的30%+",
                    "供应链储备充足，量产爬坡确定性较高",
                    "客户反馈积极，首批预订数据超预期",
                ],
                "counter": [
                    "新品爬坡存在技术和良率风险",
                    "竞品可能快速跟进推出类似产品",
                ],
                "triggers": [
                    "首批交付完成且口碑发酵",
                    "月度产销数据持续超预期",
                    "获得重大客户认证或订单",
                ],
                "invalidations": [
                    "良率迟迟未达经济性水平",
                    "出现严重质量问题或召回",
                ],
                "horizon": "MEDIUM_TERM",
                "risk_notes": "新产品放量节奏是影响股价的关键变量，需逐月跟踪。警惕PPT产品（仅发布不落地）。",
            },
            {
                "hypothesis": "{assets}产品矩阵完善夯实竞争优势，有望复制成功产品的增长曲线。",
                "impact_chain": "新品补充产品线 -> 交叉销售机会 -> {assets}客单价提升 -> ARPU增长 -> 估值上移",
                "supporting": [
                    "新品与现有产品形成良好互补，不相互蚕食",
                    "品牌认知度高，新品推广成本低",
                    "渠道复用程度高，新品可快速铺开",
                ],
                "counter": [
                    "产品线过度扩张可能导致资源分散",
                    "新品可能蚕食原有高端产品份额",
                ],
                "triggers": [
                    "新品首季销售数据公布",
                    "获得行业权威评测认可",
                ],
                "invalidations": [
                    "新品市场反响平平",
                    "出现定价失误或定位模糊",
                ],
                "horizon": "SHORT_TERM",
                "risk_notes": "产品发布到业绩兑现存在半年以上的滞后，股价炒作可能提前透支。关注首发用户的真实反馈。",
            },
        ],
        "geopolitical": [
            {
                "hypothesis": "地缘政治紧张局势利好避险资产和国产替代标的，{assets}受益于供应链重构逻辑。",
                "impact_chain": "地缘事件 -> 风险偏好骤降 -> 资金流向安全资产 -> {assets}（国产替代）获得政策加码 -> 订单转移",
                "supporting": [
                    "供应链去风险化成为全球趋势，国产化率政策目标明确",
                    "{assets}在国内市场已具备替代能力，技术差距缩小",
                    "政策端明确支持自主可控，政府采购倾斜力度加大",
                ],
                "counter": [
                    "技术差距在某些高端领域仍然显著",
                    "完全脱钩不现实，中间路线可能延后替代进程",
                ],
                "triggers": [
                    "制裁清单扩大或技术限制升级",
                    "国产替代政策文件密集出台",
                    "关键客户验证通过或小批量供货",
                ],
                "invalidations": [
                    "外交关系缓和",
                    "国产产品重大技术事故",
                ],
                "horizon": "MEDIUM_TERM",
                "risk_notes": "地缘政治事件高度不可预测，主题炒作成分大。国产替代需要关注技术进展和客户验证节奏。",
            },
            {
                "hypothesis": "中美摩擦升级利空出口导向型{assets}，建议回避海外收入占比高的标的。",
                "impact_chain": "关税/制裁 -> 海外收入预期下调 -> {assets}盈利预测下修 -> 估值折价 -> 资金撤离",
                "supporting": [
                    "公司海外收入占比超40%，受冲击弹性大",
                    "过往贸易摩擦期间该板块平均回撤25%",
                    "供应链迁移至第三国存在时间和成本障碍",
                ],
                "counter": [
                    "公司可能通过转口贸易对冲部分影响",
                    "人民币贬值部分对冲关税影响",
                ],
                "triggers": [
                    "关税清单正式公布",
                    "公司下调海外业绩指引",
                ],
                "invalidations": [
                    "达成贸易协议",
                    "公司成功转移产能至第三国",
                ],
                "horizon": "SHORT_TERM",
                "risk_notes": "贸易摩擦影响具有突发性，且可能持续升级。出口型企业风险敞口需要动态评估。",
            },
        ],
        "industry_disruption": [
            {
                "hypothesis": "供应链扰动导致{assets}供需失衡，价格弹性带来的利润弹性远超市场预期。",
                "impact_chain": "供应中断 -> 产品涨价 -> {assets}毛利率跳升 -> 季度利润大增 -> 股价上行",
                "supporting": [
                    "供给缺口短期难以弥补，新产能建设周期至少12个月",
                    "下游客户对价格敏感度低，涨价传导顺畅",
                    "公司库存处于低位，直接受益于现货价格上涨",
                ],
                "counter": [
                    "供应链恢复速度快于预期可能迅速逆转价格",
                    "政策干预可能平抑价格",
                ],
                "triggers": [
                    "供应端突发停产公告",
                    "现货价格突破历史高位",
                    "公司公告产能利用率逼近上限",
                ],
                "invalidations": [
                    "替代产能迅速释放",
                    "需求大幅萎缩",
                ],
                "horizon": "SHORT_TERM",
                "risk_notes": "供给冲击驱动的行情往往来去匆匆，追高风险大。建议在事件初期介入，注意及时止盈。",
            },
        ],
        "management_change": [
            {
                "hypothesis": "新管理层有望带来经营变革，{assets}或迎来拐点性机会，但需要1-2个季度验证。",
                "impact_chain": "高管变更 -> 市场预期调整 -> {assets}战略调整 -> 业务指标验证 -> 估值重估",
                "supporting": [
                    "新任管理者在过往任职履历中业绩出色",
                    "公司近年经营疲弱，变革动力和空间都较大",
                    "新任管理者可能带来新的战略资源和业务关系",
                ],
                "counter": [
                    "管理层变动初期存在团队磨合和战略不确定性",
                    "历史数据显示高管变更后一年内跑赢概率约55%",
                ],
                "triggers": [
                    "新管理层发布战略规划",
                    "组织架构或核心岗位调整完成",
                ],
                "invalidations": [
                    "新管理层与董事会产生重大分歧",
                    "核心骨干跟随前管理层离职",
                ],
                "horizon": "MEDIUM_TERM",
                "risk_notes": "管理层变更是典型的高不确定性事件，建议等待1-2季度经营数据验证方向后再做判断。",
            },
        ],
        "market_anomaly": [
            {
                "hypothesis": "{assets}出现交易异动，可能是资金提前布局的迹象，建议跟踪但暂勿追高。",
                "impact_chain": "异动信号 -> 市场关注度提升 -> {assets}短线博弈 -> 真实逻辑浮现或证伪 -> 方向性行情",
                "supporting": [
                    "龙虎榜显示机构席位参与，非游资主导",
                    "成交量放大伴随价格突破关键均线",
                    "板块效应明显，同行业多只个股同步异动",
                ],
                "counter": [
                    "纯资金驱动的行情缺乏基本面支撑，回落速度快",
                    "异动可能是主力出货的前兆",
                ],
                "triggers": [
                    "公司发布异动公告或澄清",
                    "成交量持续放大且股价站稳新高",
                ],
                "invalidations": [
                    "异动后成交量快速萎缩",
                    "公司公告否定市场传闻",
                ],
                "horizon": "SHORT_TERM",
                "risk_notes": "市场异动分析具有较高不确定性，可能是噪音而非信号。建议等待基本面或消息面验证。",
            },
        ],
        "other": [
            {
                "hypothesis": "{assets}受该事件影响存在一定不确定性，建议中性观望，等待更多信息明朗后再做判断。",
                "impact_chain": "事件发生 -> 市场消化信息 -> {assets}价格波动 -> 信息明朗 -> 方向确认",
                "supporting": [
                    "事件本身具有一定的市场关注度",
                    "历史同类事件对资产价格的影响存在统计规律",
                ],
                "counter": [
                    "事件信息尚不充分，难以准确评估影响",
                    "市场可能已经反映部分预期",
                ],
                "triggers": [
                    "更多关键信息披露",
                    "权威机构发布分析报告",
                ],
                "invalidations": [
                    "事件被证实为误读或夸大",
                ],
                "horizon": "SHORT_TERM",
                "risk_notes": "信息不充分时不宜做方向性判断，建议等待信息完整后再做决策。本研究仅基于公开信息，不构成投资建议。",
            },
        ],
    }

    def _get_hypothesis_templates(self, event_type: str) -> list[dict]:
        """Get templates for event_type, falling back to 'other'."""
        if event_type in self._HYPOTHESIS_TEMPLATES:
            return self._HYPOTHESIS_TEMPLATES[event_type]
        return self._HYPOTHESIS_TEMPLATES["other"]