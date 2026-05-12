import logging
from typing import Optional

from app.models.market_event import MarketEvent

logger = logging.getLogger(__name__)


class EventAlphaScorer:
    """Computes an event alpha score (0.0-1.0) from multi-dimensional event signals.

    The score is a weighted linear combination of:
    - novelty: how surprising the event is
    - materiality: how financially significant
    - credibility: trustworthiness of the source/analysis
    - urgency: how immediate the market reaction needs to be
    - confidence: LLM's own confidence in the extraction
    - tradability: ease of translating the signal into a trade
    - liquidity: depth of the market for the linked assets
    - risk: disruption/uncertainty penalty (negative weight)
    """

    W_NOVELTY: float = 0.20
    W_MATERIALITY: float = 0.20
    W_CREDIBILITY: float = 0.15
    W_URGENCY: float = 0.15
    W_CONFIDENCE: float = 0.10
    W_TRADABILITY: float = 0.10
    W_LIQUIDITY: float = 0.10
    W_RISK: float = -0.20

    def compute(
        self,
        novelty: float,
        materiality: float,
        credibility: float,
        urgency: float,
        confidence: float,
        tradability: float = 0.5,
        liquidity: float = 0.5,
        risk: float = 0.3,
    ) -> float:
        """Compute the raw alpha score from component values.

        All component values should be in [0.0, 1.0].
        """
        score = (
            self.W_NOVELTY * novelty
            + self.W_MATERIALITY * materiality
            + self.W_CREDIBILITY * credibility
            + self.W_URGENCY * urgency
            + self.W_CONFIDENCE * confidence
            + self.W_TRADABILITY * tradability
            + self.W_LIQUIDITY * liquidity
            + self.W_RISK * risk
        )
        return round(max(0.0, min(1.0, score)), 6)


# Singleton instance
_scorer = EventAlphaScorer()


async def score_event(event: MarketEvent) -> MarketEvent:
    """Compute the alpha score for a MarketEvent and persist it.

    Uses the EventAlphaScorer weighted model to combine the event's
    component scores into a single 0.0-1.0 alpha score.

    Args:
        event: A MarketEvent model instance with populated component scores.

    Returns:
        The same MarketEvent instance with event_alpha_score populated.
    """
    try:
        # Derive credibility from confidence if not explicitly set
        credibility = getattr(event, "credibility_score", None)
        if credibility is None:
            credibility = event.confidence_score * 0.85  # slightly discounted

        # Use default tradability/liquidity based on market_scope
        market_scope = (event.market_scope or "").upper()
        if market_scope in ("A_SHARE", "HK_SHARE"):
            tradability = 0.70
            liquidity = 0.65
        elif market_scope == "BOTH":
            tradability = 0.80
            liquidity = 0.75
        else:
            tradability = 0.50
            liquidity = 0.50

        # Scale risk: normalize risk_score into penalty, invert for weighting
        # (higher risk_score means higher risk, which reduces alpha)
        risk_penalty = event.risk_score if event.risk_score else 0.3

        alpha = _scorer.compute(
            novelty=event.novelty_score or 0.0,
            materiality=event.materiality_score or 0.0,
            credibility=credibility or 0.5,
            urgency=event.urgency_score or 0.0,
            confidence=event.confidence_score or 0.0,
            tradability=tradability,
            liquidity=liquidity,
            risk=risk_penalty,
        )

        event.event_alpha_score = alpha
        logger.debug(
            "Computed alpha score %.4f for event %s (type=%s)",
            alpha,
            event.id,
            event.event_type,
        )
        return event

    except Exception:
        logger.exception("Failed to compute alpha score for event %s", getattr(event, "id", "unknown"))
        # Set a safe default rather than crashing
        event.event_alpha_score = 0.30
        return event