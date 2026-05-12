import pytest
from pydantic import ValidationError
from app.schemas.llm_outputs import (
    ExtractedEventOutput,
    AssetLinkOutput,
    AssetMappingOutput,
    HypothesisOutput,
)


class TestExtractedEventOutput:
    def test_valid_output(self):
        data = {
            "event_type": "earnings_surprise",
            "event_summary": "Company X reported strong earnings",
            "primary_entity": "Company X",
            "related_entities": ["Sector Y"],
            "market_scope": "A_SHARE",
            "direction": "POSITIVE",
            "materiality_score": 0.8,
            "novelty_score": 0.6,
            "urgency_score": 0.7,
            "confidence_score": 0.9,
            "risk_score": 0.2,
            "reasoning_summary": "Strong earnings typically drive price appreciation",
            "risk_flags": ["Earnings may be one-time event"],
        }
        result = ExtractedEventOutput(**data)
        assert result.event_type == "earnings_surprise"
        assert result.materiality_score == 0.8

    def test_scores_must_be_in_range(self):
        with pytest.raises(ValidationError):
            ExtractedEventOutput(
                event_type="other",
                event_summary="test",
                primary_entity="test",
                materiality_score=1.5,  # out of range
                novelty_score=0.5,
                urgency_score=0.5,
                confidence_score=0.5,
                risk_score=0.5,
                market_scope="UNKNOWN",
                direction="UNKNOWN",
                reasoning_summary="test",
            )

    def test_negative_score_rejected(self):
        with pytest.raises(ValidationError):
            ExtractedEventOutput(
                event_type="other",
                event_summary="test",
                primary_entity="test",
                materiality_score=-0.1,
                novelty_score=0.5,
                urgency_score=0.5,
                confidence_score=0.5,
                risk_score=0.5,
                market_scope="UNKNOWN",
                direction="UNKNOWN",
                reasoning_summary="test",
            )


class TestAssetMappingOutput:
    def test_valid_output(self):
        data = {
            "asset_links": [
                {
                    "symbol": "600519.SH",
                    "name": "Moutai",
                    "market": "A_SHARE",
                    "impact_direction": "POSITIVE",
                    "impact_strength": 0.8,
                    "reason": "Direct beneficiary",
                    "confidence_score": 0.7,
                }
            ]
        }
        result = AssetMappingOutput(**data)
        assert len(result.asset_links) == 1
        assert result.asset_links[0].symbol == "600519.SH"


class TestHypothesisOutput:
    def test_valid_output(self):
        data = {
            "hypothesis_text": "The policy change will benefit sector X",
            "impact_chain": "Policy → Sector Growth → Stock Appreciation",
            "supporting_evidence": ["Historical precedent A", "Expert opinion B"],
            "counter_evidence": ["Regulatory uncertainty"],
            "trigger_conditions": ["Policy implementation confirmed"],
            "invalidation_conditions": ["Policy reversed"],
            "time_horizon": "MEDIUM_TERM",
            "risk_notes": "Execution risk remains",
        }
        result = HypothesisOutput(**data)
        assert result.hypothesis_text == data["hypothesis_text"]
        assert len(result.supporting_evidence) == 2