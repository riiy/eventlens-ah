import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market_event import MarketEvent
from app.models.raw_document import RawDocument

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard-level queries and aggregations."""

    async def get_summary(
        self, session: AsyncSession
    ) -> dict:
        """Get a high-level summary of the system state.

        Returns a dict compatible with the DashboardSummary schema.
        """
        # Total documents
        doc_count_result = await session.execute(
            select(func.count()).select_from(RawDocument)
        )
        total_documents = doc_count_result.scalar() or 0

        # Total events
        event_count_result = await session.execute(
            select(func.count()).select_from(MarketEvent)
        )
        total_events = event_count_result.scalar() or 0

        # High-score events (alpha >= 0.7)
        high_score_result = await session.execute(
            select(func.count()).select_from(MarketEvent).where(
                MarketEvent.event_alpha_score >= 0.7
            )
        )
        high_score_events = high_score_result.scalar() or 0

        # Pending events (not yet scored, hypothesized, or archived)
        pending_result = await session.execute(
            select(func.count()).select_from(MarketEvent).where(
                MarketEvent.status.notin_(["SCORED", "HYPOTHESIZED", "ARCHIVED"])
            )
        )
        pending_events = pending_result.scalar() or 0

        # Event type distribution
        type_dist_result = await session.execute(
            select(
                MarketEvent.event_type,
                func.count(MarketEvent.id),
            ).group_by(MarketEvent.event_type)
        )
        event_type_distribution = {
            row[0]: row[1] for row in type_dist_result.all()
        }

        return {
            "total_documents": total_documents,
            "total_events": total_events,
            "high_score_events": high_score_events,
            "pending_events": pending_events,
            "event_type_distribution": event_type_distribution,
        }

    async def get_top_events(
        self, session: AsyncSession, limit: int = 10
    ) -> list[MarketEvent]:
        """Get top events ordered by event_alpha_score descending."""
        result = await session.execute(
            select(MarketEvent)
            .where(MarketEvent.event_alpha_score > 0)
            .order_by(MarketEvent.event_alpha_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent_documents(
        self, session: AsyncSession, limit: int = 10
    ) -> list[RawDocument]:
        """Get the most recently created documents."""
        result = await session.execute(
            select(RawDocument)
            .order_by(RawDocument.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())