import random
from uuid import UUID

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event_asset_link import EventAssetLink
from app.models.event_price_reaction import EventPriceReaction
from app.models.research_hypothesis import ResearchHypothesis


class HypothesisService:
    """Service for reading research hypotheses and price reactions."""

    async def get_for_event(
        self, session: AsyncSession, event_id: UUID
    ) -> list[ResearchHypothesis]:
        """Get all hypotheses linked to a specific event."""
        result = await session.execute(
            select(ResearchHypothesis).where(
                ResearchHypothesis.event_id == event_id
            )
        )
        return list(result.scalars().all())

    async def get_price_reactions(
        self, session: AsyncSession, event_id: UUID
    ) -> list[EventPriceReaction]:
        """Get all price reactions linked to a specific event."""
        result = await session.execute(
            select(EventPriceReaction).where(
                EventPriceReaction.event_id == event_id
            )
        )
        return list(result.scalars().all())

    async def generate_mock_price_reactions(
        self, session: AsyncSession, event_id: UUID
    ) -> list[EventPriceReaction]:
        """Generate mock price reaction data for an event based on linked assets."""
        links_result = await session.execute(
            select(EventAssetLink).where(EventAssetLink.event_id == event_id)
        )
        links = list(links_result.scalars().all())
        if not links:
            logger.warning(
                "No linked assets for event {}, cannot generate reactions", event_id
            )
            return []

        reactions = []
        for link in links:
            direction_mult = 1.0 if link.impact_direction == "POSITIVE" else -1.0 if link.impact_direction == "NEGATIVE" else 0.0
            base_return = random.uniform(0.01, 0.06) * direction_mult * link.impact_strength

            reaction = EventPriceReaction(
                event_id=event_id,
                asset_id=link.asset_id,
                return_1d=round(base_return + random.uniform(-0.01, 0.01), 4),
                return_3d=round(base_return * 1.5 + random.uniform(-0.02, 0.02), 4),
                return_5d=round(base_return * 2.0 + random.uniform(-0.03, 0.03), 4),
                return_20d=round(base_return * 3.5 + random.uniform(-0.05, 0.05), 4),
                max_drawdown=round(random.uniform(-0.03, -0.001) * direction_mult, 4),
                volume_change=round(random.uniform(0.1, 2.5) * link.impact_strength, 4),
                benchmark_return=round(base_return * 0.3 + random.uniform(-0.01, 0.01), 4),
                excess_return=round(base_return - base_return * 0.3, 4),
                notes=f"Mock reaction for {link.impact_direction} impact (strength: {link.impact_strength})",
                asset_name=link.asset_name,
                asset_symbol=link.asset_symbol,
            )
            session.add(reaction)
            reactions.append(reaction)

        await session.flush()
        logger.info(
            "Generated {} mock price reactions for event {}", len(reactions), event_id
        )
        return reactions
