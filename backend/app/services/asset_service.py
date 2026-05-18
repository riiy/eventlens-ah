from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.asset import Asset
from app.schemas.asset import AssetCreate


class AssetService:
    """Service for Asset CRUD operations."""

    async def create(
        self, session: AsyncSession, data: AssetCreate
    ) -> Asset:
        """Create a new Asset."""
        asset = Asset(
            symbol=data.symbol,
            name=data.name,
            market=data.market,
            exchange=data.exchange,
            sector=data.sector,
            industry=data.industry,
            business_tags=data.business_tags,
        )
        session.add(asset)
        await session.flush()
        logger.info("Created Asset id={} symbol={}", asset.id, asset.symbol)
        return asset

    async def get(
        self, session: AsyncSession, asset_id: UUID
    ) -> Asset | None:
        """Get a single Asset by ID."""
        result = await session.execute(
            select(Asset).where(Asset.id == asset_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        session: AsyncSession,
        offset: int = 0,
        limit: int = 20,
        market: str | None = None,
        sector: str | None = None,
    ) -> tuple[list[Asset], int]:
        """List Assets with optional filtering and pagination.

        Returns a tuple of (items, total_count).
        """
        conditions = []

        if market is not None:
            conditions.append(Asset.market == market)
        if sector is not None:
            conditions.append(Asset.sector == sector)

        # Count query
        count_stmt = select(func.count()).select_from(Asset)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Items query
        items_stmt = (
            select(Asset)
            .order_by(Asset.symbol.asc())
            .offset(offset)
            .limit(limit)
        )
        if conditions:
            items_stmt = items_stmt.where(*conditions)
        items_result = await session.execute(items_stmt)
        items = list(items_result.scalars().all())

        return items, total

    async def get_by_symbol(
        self, session: AsyncSession, symbol: str
    ) -> Asset | None:
        """Get an Asset by its symbol."""
        result = await session.execute(
            select(Asset).where(Asset.symbol == symbol)
        )
        return result.scalar_one_or_none()
