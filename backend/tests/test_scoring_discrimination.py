import pytest
from app.scoring.scorer import EventAlphaScorer


class TestScoringDiscrimination:
    """Verify the scorer has real discrimination power, not just decorative."""

    def setup_method(self):
        self.scorer = EventAlphaScorer()

    def _score(self, materiality, novelty, credibility, urgency, risk,
               confidence=0.5, tradability=0.5, liquidity=0.5):
        return self.scorer.compute(
            novelty=novelty, materiality=materiality,
            credibility=credibility, urgency=urgency,
            confidence=confidence, tradability=tradability,
            liquidity=liquidity, risk=risk,
        )

    def test_high_value_events_beat_low_value(self):
        high_value = self._score(
            materiality=0.85, novelty=0.90, credibility=0.80,
            urgency=0.70, risk=0.15,
        )
        low_value = self._score(
            materiality=0.15, novelty=0.10, credibility=0.20,
            urgency=0.10, risk=0.90,
        )
        assert high_value > low_value
        assert high_value - low_value > 0.25

    def test_rumors_low_credibility_matters(self):
        credible = self._score(
            materiality=0.70, novelty=0.70, credibility=0.90,
            urgency=0.50, risk=0.30,
        )
        rumor = self._score(
            materiality=0.70, novelty=0.70, credibility=0.15,
            urgency=0.50, risk=0.30,
        )
        assert credible > rumor
        assert credible - rumor > 0.08

    def test_old_news_low_novelty_matters(self):
        fresh = self._score(
            materiality=0.70, novelty=0.90, credibility=0.60,
            urgency=0.50, risk=0.30,
        )
        old = self._score(
            materiality=0.70, novelty=0.10, credibility=0.60,
            urgency=0.50, risk=0.30,
        )
        assert fresh > old
        assert fresh - old > 0.12

    def test_high_risk_penalizes(self):
        low_risk = self._score(
            materiality=0.70, novelty=0.70, credibility=0.60,
            urgency=0.50, risk=0.10,
        )
        high_risk = self._score(
            materiality=0.70, novelty=0.70, credibility=0.60,
            urgency=0.50, risk=0.90,
        )
        assert low_risk > high_risk
        assert low_risk - high_risk > 0.12

    def test_not_all_bullish_high_score(self):
        score = self._score(
            materiality=0.90, novelty=0.05, credibility=0.10,
            urgency=0.30, risk=0.95,
        )
        assert score < 0.35

    def test_quality_bearish_can_score_high(self):
        score = self._score(
            materiality=0.90, novelty=0.85, credibility=0.90,
            urgency=0.80, risk=0.10, confidence=0.90,
            tradability=0.80, liquidity=0.75,
        )
        assert score > 0.65

    def test_score_spread_is_wide(self):
        cases = [
            (0.90, 0.85, 0.90, 0.80, 0.05, 0.85, 0.90, 0.80),
            (0.85, 0.90, 0.70, 0.75, 0.10, 0.70, 0.75, 0.70),
            (0.80, 0.80, 0.80, 0.70, 0.15, 0.65, 0.70, 0.65),
            (0.75, 0.70, 0.85, 0.65, 0.20, 0.60, 0.65, 0.60),
            (0.70, 0.75, 0.60, 0.60, 0.25, 0.55, 0.60, 0.55),
            (0.60, 0.50, 0.70, 0.55, 0.35, 0.50, 0.50, 0.50),
            (0.50, 0.55, 0.65, 0.50, 0.40, 0.50, 0.50, 0.50),
            (0.50, 0.40, 0.50, 0.45, 0.50, 0.50, 0.50, 0.50),
            (0.40, 0.30, 0.55, 0.40, 0.55, 0.50, 0.50, 0.50),
            (0.35, 0.25, 0.30, 0.35, 0.65, 0.50, 0.50, 0.50),
            (0.30, 0.20, 0.40, 0.30, 0.70, 0.50, 0.50, 0.50),
            (0.25, 0.15, 0.25, 0.25, 0.75, 0.50, 0.50, 0.50),
            (0.20, 0.10, 0.35, 0.20, 0.80, 0.50, 0.50, 0.50),
            (0.10, 0.05, 0.20, 0.10, 0.90, 0.50, 0.50, 0.50),
            (0.05, 0.05, 0.10, 0.05, 0.95, 0.50, 0.50, 0.50),
            (0.80, 0.10, 0.90, 0.50, 0.30, 0.50, 0.50, 0.50),
            (0.80, 0.80, 0.10, 0.50, 0.30, 0.50, 0.50, 0.50),
            (0.10, 0.80, 0.80, 0.50, 0.90, 0.50, 0.50, 0.50),
            (0.50, 0.50, 0.10, 0.50, 0.90, 0.50, 0.50, 0.50),
            (0.95, 0.95, 0.10, 0.95, 0.95, 0.50, 0.50, 0.50),
        ]
        scores = [self._score(*c) for c in cases]
        spread = max(scores) - min(scores)
        assert spread > 0.35, f"Score spread too narrow: {spread:.3f}"

        low_count = sum(1 for s in scores if s < 0.4)
        assert low_count >= 3, f"Not enough low scores: {low_count}/20 below 0.4"

        high_count = sum(1 for s in scores if s > 0.7)
        assert high_count >= 3, f"Not enough high scores: {high_count}/20 above 0.7"