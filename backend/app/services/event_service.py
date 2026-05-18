from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import get_llm_provider
from app.llm.mock_provider import MockLLMProvider
from app.models.asset import Asset
from app.models.event_asset_link import EventAssetLink
from app.models.llm_run_log import LLMRunLog
from app.models.market_event import MarketEvent
from app.models.research_hypothesis import ResearchHypothesis
from app.schemas.llm_outputs import ExtractedEventOutput
from app.schemas.market_event import MarketEventCreate
from app.scoring import score_event

from loguru import logger


class EventService:
    """Service for MarketEvent CRUD and the event extraction pipeline."""

    @staticmethod
    def _fallback_llm_provider(llm: object, exc: Exception) -> MockLLMProvider | None:
        if isinstance(exc, NotImplementedError) and not isinstance(llm, MockLLMProvider):
            logger.warning(
                "Configured LLM provider {} is not implemented; falling back to MockLLMProvider",
                type(llm).__name__,
            )
            return MockLLMProvider()
        return None

    async def create(
        self, session: AsyncSession, data: MarketEventCreate
    ) -> MarketEvent:
        """Create a new MarketEvent."""
        event = MarketEvent(
            raw_document_id=data.raw_document_id,
            event_type=data.event_type,
            event_summary=data.event_summary,
            primary_entity=data.primary_entity,
            related_entities=data.related_entities,
            market_scope=data.market_scope,
            direction=data.direction,
        )
        session.add(event)
        await session.flush()
        logger.info("Created MarketEvent id={} type={}", event.id, event.event_type)
        return event

    async def get(
        self, session: AsyncSession, event_id: UUID
    ) -> MarketEvent | None:
        """Get a single MarketEvent by ID."""
        result = await session.execute(
            select(MarketEvent).where(MarketEvent.id == event_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        session: AsyncSession,
        offset: int = 0,
        limit: int = 20,
        event_type: str | None = None,
        market_scope: str | None = None,
        direction: str | None = None,
        status: str | None = None,
        min_score: float | None = None,
        max_score: float | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[MarketEvent], int]:
        """List MarketEvents with filtering and pagination.

        Returns a tuple of (items, total_count).
        """
        conditions = []

        if event_type is not None:
            conditions.append(MarketEvent.event_type == event_type)
        if market_scope is not None:
            conditions.append(MarketEvent.market_scope == market_scope)
        if direction is not None:
            conditions.append(MarketEvent.direction == direction)
        if status is not None:
            conditions.append(MarketEvent.status == status)
        if min_score is not None:
            conditions.append(MarketEvent.event_alpha_score >= min_score)
        if max_score is not None:
            conditions.append(MarketEvent.event_alpha_score <= max_score)
        if date_from is not None:
            conditions.append(MarketEvent.created_at >= date_from)
        if date_to is not None:
            conditions.append(MarketEvent.created_at <= date_to)

        # Count query
        count_stmt = select(func.count()).select_from(MarketEvent)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Sort column
        sort_col = getattr(MarketEvent, sort_by, MarketEvent.created_at)
        if sort_order == "asc":
            order_clause = sort_col.asc()
        else:
            order_clause = sort_col.desc()

        # Items query
        items_stmt = (
            select(MarketEvent)
            .order_by(order_clause)
            .offset(offset)
            .limit(limit)
        )
        if conditions:
            items_stmt = items_stmt.where(*conditions)
        items_result = await session.execute(items_stmt)
        items = list(items_result.scalars().all())

        return items, total

    async def _record_llm_run_log(
        self,
        session: AsyncSession,
        task_type: str,
        model_name: str,
        prompt_version: str,
        input_data: dict,
        output_json: dict | None,
        error_message: str | None,
        latency_ms: int,
    ) -> None:
        input_hash = hashlib.sha256(
            json.dumps(input_data, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        logger.info(
            "Recording LLM run log: task_type={}, model_name={}, prompt_version={}",
            task_type,
            model_name,
            prompt_version,
        )
        log = LLMRunLog(
            task_type=task_type,
            model_name=model_name,
            prompt_version=prompt_version,
            input_hash=input_hash,
            output_json=output_json,
            error_message=error_message,
            latency_ms=latency_ms,
        )
        session.add(log)

    async def _extract_event_output(
        self,
        session: AsyncSession,
        document_id: UUID,
        task_type: str = "extract_event",
        prompt_version: str = "v1",
    ) -> tuple[object | None, ExtractedEventOutput | None]:
        from app.models.raw_document import RawDocument

        doc_result = await session.execute(
            select(RawDocument).where(RawDocument.id == document_id)
        )
        doc = doc_result.scalar_one_or_none()
        if doc is None:
            logger.warning("Document not found: {}", document_id)
            return None, None

        published_at_str = ""
        if doc.published_at is not None:
            published_at_str = doc.published_at.isoformat()

        llm = get_llm_provider()
        input_data = {
            "title": doc.title,
            "content": doc.content,
            "source": doc.source,
            "published_at": published_at_str,
        }
        start = time.monotonic()

        try:
            try:
                extracted = await llm.extract_event(
                    title=doc.title,
                    content=doc.content,
                    source=doc.source,
                    published_at=published_at_str,
                )
            except Exception as exc:
                fallback_llm = self._fallback_llm_provider(llm, exc)
                if fallback_llm is None:
                    raise
                llm = fallback_llm
                extracted = await llm.extract_event(
                    title=doc.title,
                    content=doc.content,
                    source=doc.source,
                    published_at=published_at_str,
                )
            latency_ms = int((time.monotonic() - start) * 1000)
            await self._record_llm_run_log(
                session,
                task_type,
                llm.model_name,
                prompt_version,
                input_data,
                extracted.model_dump(),
                None,
                latency_ms,
            )
            return doc, extracted
        except Exception as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            await self._record_llm_run_log(
                session,
                task_type,
                llm.model_name,
                prompt_version,
                input_data,
                None,
                str(exc),
                latency_ms,
            )
            logger.exception("Failed to extract event from document {}", document_id)
            return doc, None

    async def extract_from_document(
        self, session: AsyncSession, document_id: UUID
    ) -> MarketEvent | None:
        """Extract a MarketEvent from a RawDocument using the LLM provider.

        Loads the document, calls the LLM to extract structured event data,
        and persists a new MarketEvent.
        """
        doc, extracted = await self._extract_event_output(session, document_id)
        if doc is None or extracted is None:
            return None

        event = MarketEvent(
            raw_document_id=doc.id,
            event_type=extracted.event_type,
            event_summary=extracted.event_summary,
            primary_entity=extracted.primary_entity,
            related_entities=extracted.related_entities,
            market_scope=extracted.market_scope,
            direction=extracted.direction,
            materiality_score=extracted.materiality_score,
            novelty_score=extracted.novelty_score,
            urgency_score=extracted.urgency_score,
            credibility_score=doc.credibility_score,
            confidence_score=extracted.confidence_score,
            risk_score=extracted.risk_score,
            status="EXTRACTED",
        )
        session.add(event)
        await session.flush()
        logger.info(
            "Extracted MarketEvent id={} type={} from document {}",
            event.id,
            event.event_type,
            document_id,
        )
        return event

    async def enrich_imported_event(
        self,
        session: AsyncSession,
        event_id: UUID,
        preserve_event_type: bool = True,
        preserve_market_scope: bool = True,
        preserve_asset_links: bool = True,
    ) -> MarketEvent | None:
        event_result = await session.execute(
            select(MarketEvent).where(MarketEvent.id == event_id)
        )
        event = event_result.scalar_one_or_none()
        if event is None:
            logger.warning("Event not found for enrichment: {}", event_id)
            return None

        doc, extracted = await self._extract_event_output(
            session,
            event.raw_document_id,
            task_type="extract_event_import_merge",
            prompt_version="import-merge-v1",
        )
        if doc is None or extracted is None:
            return None

        if not preserve_event_type and extracted.event_type:
            event.event_type = extracted.event_type
        if extracted.event_summary and (
            not event.event_summary
            or event.event_type == "UNKNOWN"
            or event.event_summary == doc.title
        ):
            event.event_summary = extracted.event_summary
        if extracted.primary_entity and not event.primary_entity:
            event.primary_entity = extracted.primary_entity
        if extracted.related_entities and not event.related_entities:
            event.related_entities = extracted.related_entities
        if not preserve_market_scope and extracted.market_scope:
            event.market_scope = extracted.market_scope
        if extracted.direction and event.direction == "UNKNOWN":
            event.direction = extracted.direction
        if not event.materiality_score:
            event.materiality_score = extracted.materiality_score
        if not event.novelty_score:
            event.novelty_score = extracted.novelty_score
        if not event.urgency_score:
            event.urgency_score = extracted.urgency_score
        if not event.confidence_score:
            event.confidence_score = extracted.confidence_score
        if not event.risk_score:
            event.risk_score = extracted.risk_score

        event.credibility_score = doc.credibility_score
        event.status = "EXTRACTED"
        session.add(event)
        await session.flush()

        if not preserve_asset_links:
            await self.map_assets(session, event.id)

        logger.info(
            "Merged enrichment into imported event {} "
            "(preserve_event_type={} preserve_market_scope={} "
            "preserve_asset_links={})",
            event_id,
            preserve_event_type,
            preserve_market_scope,
            preserve_asset_links,
        )
        return event

    async def map_assets(
        self, session: AsyncSession, event_id: UUID
    ) -> list[EventAssetLink]:
        """Map an event to relevant assets using the LLM provider.

        Loads the event and all available assets, calls the LLM to determine
        which assets are relevant, and creates EventAssetLink records.
        """
        # Load the event
        event_result = await session.execute(
            select(MarketEvent).where(MarketEvent.id == event_id)
        )
        event = event_result.scalar_one_or_none()
        if event is None:
            logger.warning("Event not found: {}", event_id)
            return []

        # Load all assets
        assets_result = await session.execute(select(Asset))
        all_assets = list(assets_result.scalars().all())

        # Convert assets to dicts for LLM
        asset_dicts: list[dict] = [
            {
                "symbol": a.symbol,
                "name": a.name,
                "market": a.market,
                "sector": a.sector,
                "industry": a.industry,
                "business_tags": a.business_tags or [],
            }
            for a in all_assets
        ]

        try:
            llm = get_llm_provider()
            input_data = {
                "event_summary": event.event_summary,
                "event_type": event.event_type,
                "primary_entity": event.primary_entity or "",
                "assets": asset_dicts,
            }
            start = time.monotonic()
            try:
                mapping = await llm.map_event_to_assets(
                    event_summary=event.event_summary,
                    event_type=event.event_type,
                    primary_entity=event.primary_entity or "",
                    assets=asset_dicts,
                )
            except Exception as exc:
                fallback_llm = self._fallback_llm_provider(llm, exc)
                if fallback_llm is None:
                    raise
                llm = fallback_llm
                mapping = await llm.map_event_to_assets(
                    event_summary=event.event_summary,
                    event_type=event.event_type,
                    primary_entity=event.primary_entity or "",
                    assets=asset_dicts,
                )
            latency_ms = int((time.monotonic() - start) * 1000)
            await self._record_llm_run_log(
                session, "map_assets", llm.model_name, "v1",
                input_data, mapping.model_dump(), None, latency_ms,
            )

            # Build a lookup map: symbol -> Asset
            asset_by_symbol: dict[str, Asset] = {
                a.symbol: a for a in all_assets
            }

            links: list[EventAssetLink] = []
            for link_output in mapping.asset_links:
                asset = asset_by_symbol.get(link_output.symbol)
                if asset is None:
                    logger.warning(
                        "Asset symbol {} not found in database, skipping",
                        link_output.symbol,
                    )
                    continue

                link = EventAssetLink(
                    event_id=event.id,
                    asset_id=asset.id,
                    impact_direction=link_output.impact_direction,
                    impact_strength=link_output.impact_strength,
                    reason=link_output.reason,
                    confidence_score=link_output.confidence_score,
                    asset_name=asset.name,
                    asset_symbol=asset.symbol,
                )
                session.add(link)
                links.append(link)

            await session.flush()
            logger.info("Mapped {} assets to event {}", len(links), event_id)
            return links

        except Exception as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            await self._record_llm_run_log(
                session, "map_assets", llm.model_name, "v1",
                input_data, None, str(exc), latency_ms,
            )
            logger.exception("Failed to map assets for event {}", event_id)
            return []

    async def generate_hypothesis(
        self, session: AsyncSession, event_id: UUID
    ) -> ResearchHypothesis | None:
        """Generate a research hypothesis for an event using the LLM.

        Loads the event and its linked assets, calls the LLM to generate
        an investment hypothesis, and updates the event status.
        """
        # Load the event
        event_result = await session.execute(
            select(MarketEvent).where(MarketEvent.id == event_id)
        )
        event = event_result.scalar_one_or_none()
        if event is None:
            logger.warning("Event not found: {}", event_id)
            return None
        logger.info(
            "Generating hypothesis for event {} type={}", event_id, event.event_type
        )
        # Load linked assets
        links_result = await session.execute(
            select(EventAssetLink).where(EventAssetLink.event_id == event_id)
        )
        links = list(links_result.scalars().all())

        if not links:
            logger.warning(
                "No linked assets found for event {}, cannot generate hypothesis",
                event_id,
            )
            return None

        # Load asset details
        asset_ids = [link.asset_id for link in links]
        assets_result = await session.execute(
            select(Asset).where(Asset.id.in_(asset_ids))
        )
        linked_assets_map = {a.id: a for a in assets_result.scalars().all()}

        linked_asset_dicts: list[dict] = []
        for link in links:
            asset = linked_assets_map.get(link.asset_id)
            if asset is not None:
                linked_asset_dicts.append({
                    "symbol": asset.symbol,
                    "name": asset.name,
                    "market": asset.market,
                    "impact_direction": link.impact_direction,
                    "impact_strength": link.impact_strength,
                    "business_tags": asset.business_tags or [],
                })

        try:
            llm = get_llm_provider()
            logger.info("Using hypothesis provider model {}", llm.model_name)
            input_data = {
                "event_summary": event.event_summary,
                "event_type": event.event_type,
                "linked_assets": linked_asset_dicts,
            }
            start = time.monotonic()
            try:
                hypothesis_output = await llm.generate_hypothesis(
                    event_summary=event.event_summary,
                    event_type=event.event_type,
                    linked_assets=linked_asset_dicts,
                )
            except Exception as exc:
                fallback_llm = self._fallback_llm_provider(llm, exc)
                if fallback_llm is None:
                    raise
                llm = fallback_llm
                hypothesis_output = await llm.generate_hypothesis(
                    event_summary=event.event_summary,
                    event_type=event.event_type,
                    linked_assets=linked_asset_dicts,
                )
            latency_ms = int((time.monotonic() - start) * 1000)
            await self._record_llm_run_log(
                session, "generate_hypothesis", llm.model_name, "v1",
                input_data, hypothesis_output.model_dump(), None, latency_ms,
            )

            hypothesis = ResearchHypothesis(
                event_id=event.id,
                hypothesis_text=hypothesis_output.hypothesis_text,
                impact_chain=[hypothesis_output.impact_chain]
                if isinstance(hypothesis_output.impact_chain, str)
                else hypothesis_output.impact_chain,
                supporting_evidence=hypothesis_output.supporting_evidence,
                counter_evidence=hypothesis_output.counter_evidence,
                trigger_conditions=hypothesis_output.trigger_conditions,
                invalidation_conditions=hypothesis_output.invalidation_conditions,
                time_horizon=hypothesis_output.time_horizon,
                risk_notes=hypothesis_output.risk_notes,
                model_used="mock",
                status="ACTIVE",
            )
            session.add(hypothesis)

            # Update event status
            event.status = "HYPOTHESIZED"
            session.add(event)

            await session.flush()
            logger.info(
                "Generated hypothesis for event {}, status updated to HYPOTHESIZED",
                event_id,
            )
            return hypothesis

        except Exception as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            await self._record_llm_run_log(
                session, "generate_hypothesis", llm.model_name, "v1",
                input_data, None, str(exc), latency_ms,
            )
            logger.exception("Failed to generate hypothesis for event {}", event_id)
            return None

    async def score(
        self, session: AsyncSession, event_id: UUID
    ) -> MarketEvent | None:
        """Score a MarketEvent using EventAlphaScorer.

        Updates the event's alpha score and status.
        """
        event_result = await session.execute(
            select(MarketEvent).where(MarketEvent.id == event_id)
        )
        event = event_result.scalar_one_or_none()
        if event is None:
            logger.warning("Event not found for scoring: {}", event_id)
            return None

        try:
            scored = await score_event(event)
            scored.status = "SCORED"
            session.add(scored)
            await session.flush()
            logger.info(
                "Scored event {} alpha={:.4f} status=SCORED",
                event_id,
                scored.event_alpha_score,
            )
            return scored
        except Exception:
            logger.exception("Failed to score event {}", event_id)
            return None
