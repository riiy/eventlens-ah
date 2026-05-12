import pytest
from app.scoring.scorer import EventAlphaScorer


class TestEventAlphaScorer:
    def setup_method(self):
        self.scorer = EventAlphaScorer()

    def test_default_parameters(self):
        score = self.scorer.compute(
            novelty=0.8, materiality=0.7, credibility=0.6,
            urgency=0.5, confidence=0.6, tradability=0.5,
            liquidity=0.5, risk=0.3,
        )
        expected = (
            0.20 * 0.8 + 0.20 * 0.7 + 0.15 * 0.6 + 0.15 * 0.5
            + 0.10 * 0.6 + 0.10 * 0.5 + 0.10 * 0.5 - 0.20 * 0.3
        )
        assert score == pytest.approx(expected, abs=1e-6)

    def test_clamps_to_zero(self):
        score = self.scorer.compute(
            novelty=0.0, materiality=0.0, credibility=0.0,
            urgency=0.0, confidence=0.0, tradability=0.0,
            liquidity=0.0, risk=1.0,
        )
        assert score == 0.0

    def test_clamps_to_one(self):
        score = self.scorer.compute(
            novelty=1.0, materiality=1.0, credibility=1.0,
            urgency=1.0, confidence=1.0, tradability=1.0,
            liquidity=1.0, risk=0.0,
        )
        assert score == 1.0

    def test_risk_penalty_reduces_score(self):
        low_risk = self.scorer.compute(
            novelty=0.5, materiality=0.5, credibility=0.5,
            urgency=0.5, confidence=0.5, risk=0.1,
        )
        high_risk = self.scorer.compute(
            novelty=0.5, materiality=0.5, credibility=0.5,
            urgency=0.5, confidence=0.5, risk=0.9,
        )
        assert low_risk > high_risk

    def test_positive_weights_sum_to_one(self):
        total = (
            self.scorer.W_NOVELTY + self.scorer.W_MATERIALITY
            + self.scorer.W_CREDIBILITY + self.scorer.W_URGENCY
            + self.scorer.W_CONFIDENCE + self.scorer.W_TRADABILITY
            + self.scorer.W_LIQUIDITY
        )
        assert total == pytest.approx(1.0, abs=1e-6)

    def test_risk_is_negative(self):
        assert self.scorer.W_RISK < 0