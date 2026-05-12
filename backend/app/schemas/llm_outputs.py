from pydantic import BaseModel, Field


class ExtractedEventOutput(BaseModel):
    event_type: str = Field(
        description=(
            "One of: earnings_surprise, policy_change, merger_acquisition, "
            "product_launch, regulatory_action, geopolitical, industry_disruption, "
            "management_change, market_anomaly, other"
        )
    )
    event_summary: str
    primary_entity: str
    related_entities: list[str] = Field(default_factory=list)
    market_scope: str = Field(description="A_SHARE, HK_SHARE, BOTH, or UNKNOWN")
    direction: str = Field(description="POSITIVE, NEGATIVE, NEUTRAL, MIXED, or UNKNOWN")
    materiality_score: float = Field(ge=0, le=1)
    novelty_score: float = Field(ge=0, le=1)
    urgency_score: float = Field(ge=0, le=1)
    confidence_score: float = Field(ge=0, le=1)
    risk_score: float = Field(ge=0, le=1)
    reasoning_summary: str
    risk_flags: list[str] = Field(default_factory=list)


class AssetLinkOutput(BaseModel):
    symbol: str
    name: str
    market: str
    impact_direction: str = Field(description="POSITIVE, NEGATIVE, NEUTRAL, or MIXED")
    impact_strength: float = Field(ge=0, le=1)
    reason: str
    confidence_score: float = Field(ge=0, le=1)


class AssetMappingOutput(BaseModel):
    asset_links: list[AssetLinkOutput]


class HypothesisOutput(BaseModel):
    hypothesis_text: str
    impact_chain: list[str]
    supporting_evidence: list[str]
    counter_evidence: list[str]
    trigger_conditions: list[str]
    invalidation_conditions: list[str]
    time_horizon: str
    risk_notes: str