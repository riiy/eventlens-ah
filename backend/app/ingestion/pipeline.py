import hashlib
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.raw_document import RawDocument
from app.schemas.raw_document import RawDocumentCreate
from app.services.document_service import DocumentService
from app.services.event_service import EventService

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Orchestrates the end-to-end ingestion pipeline.

    The pipeline flows through these stages:
    1. Ingest raw document (dedup by content_hash)
    2. Extract market event via LLM
    3. Map event to relevant assets via LLM
    4. Score the event alpha
    5. Generate investment hypothesis via LLM
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_service = DocumentService()
        self.event_service = EventService()

    async def ingest_document(self, data: dict) -> RawDocument:
        """Ingest a single document from a dict, deduplicating by content hash.

        Expects a dict with keys matching RawDocumentCreate fields plus optional
        extra fields that will be passed through to the RawDocument constructor.
        """
        content = data.get("content", "")
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # Check for existing document
        result = await self.session.execute(
            select(RawDocument).where(RawDocument.content_hash == content_hash)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            logger.debug(
                "Document with hash=%s already exists (id=%s)", content_hash, existing.id
            )
            return existing

        # Build RawDocumentCreate from dict
        create_data = RawDocumentCreate(
            source=data.get("source", "unknown"),
            source_type=data.get("source_type", "manual"),
            url=data.get("url"),
            title=data.get("title", ""),
            content=content,
            language=data.get("language", "zh"),
            published_at=data.get("published_at"),
        )

        doc = RawDocument(
            source=create_data.source,
            source_type=create_data.source_type,
            url=create_data.url,
            title=create_data.title,
            content=create_data.content,
            language=create_data.language,
            published_at=create_data.published_at,
            content_hash=content_hash,
            credibility_score=data.get("credibility_score", 0.5),
            metadata_json=data.get("metadata_json"),
        )
        self.session.add(doc)
        await self.session.flush()
        logger.info("Ingested document id=%s hash=%s", doc.id, content_hash)
        return doc

    async def run_demo(self) -> dict:
        """Run the full pipeline against demo/seed documents.

        1. Fetch seed documents from DemoIngestionSource
        2. Insert each document (dedup by content_hash)
        3. For each new document, run the full pipeline
        4. Commit and return summary counts

        Returns a dict with counts of what was processed.
        """
        from app.ingestion.sources import DemoIngestionSource

        source = DemoIngestionSource()
        documents = await source.fetch()

        documents_ingested = 0
        events_extracted = 0

        for doc_data in documents:
            # Compute hash to check if new
            content = doc_data.get("content", "")
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

            # Check dedup
            result = await self.session.execute(
                select(RawDocument).where(
                    RawDocument.content_hash == content_hash
                )
            )
            existing = result.scalar_one_or_none()

            if existing is not None:
                logger.debug("Skipping existing document hash=%s", content_hash)
                # Check if events already exist for this document
                existing_events_result = await self.session.execute(
                    select(RawDocument).where(
                        RawDocument.id == existing.id
                    )
                )
                # If document already has processed events, skip pipeline stages
                continue

            # Ingest the document
            doc = await self.ingest_document(doc_data)
            documents_ingested += 1

            # Run full pipeline for the new document
            try:
                pipeline_result = await self.run_full_pipeline(doc.id)
                if pipeline_result.get("event_id") is not None:
                    events_extracted += 1
            except Exception:
                logger.exception(
                    "Pipeline failed for document %s, continuing with next",
                    doc.id,
                )

        await self.session.commit()

        logger.info(
            "Demo ingestion complete: %d documents ingested, %d events extracted",
            documents_ingested,
            events_extracted,
        )

        return {
            "assets_created": 0,  # Assets are pre-seeded, not created by pipeline
            "documents_ingested": documents_ingested,
            "events_extracted": events_extracted,
            "message": (
                f"Demo ingestion complete. "
                f"Ingested {documents_ingested} documents, "
                f"extracted {events_extracted} events."
            ),
        }

    async def run_full_pipeline(self, document_id: UUID) -> dict:
        """Run the complete pipeline for a single document.

        Stages: Extract -> Map Assets -> Score -> Generate Hypothesis

        Returns a dict with the IDs of created entities.
        """
        result: dict = {
            "document_id": str(document_id),
            "event_id": None,
            "asset_link_count": 0,
            "hypothesis_id": None,
            "alpha_score": None,
            "errors": [],
        }

        # Stage 1: Extract event
        try:
            event = await self.event_service.extract_from_document(
                self.session, document_id
            )
            if event is None:
                result["errors"].append("event_extraction_failed")
                return result
            result["event_id"] = str(event.id)
        except Exception as e:
            logger.exception("Event extraction failed for doc %s", document_id)
            result["errors"].append(f"event_extraction_error: {e}")
            return result

        # Stage 2: Map assets
        try:
            links = await self.event_service.map_assets(
                self.session, event.id
            )
            result["asset_link_count"] = len(links)
        except Exception as e:
            logger.exception("Asset mapping failed for event %s", event.id)
            result["errors"].append(f"asset_mapping_error: {e}")

        # Stage 3: Score
        try:
            scored = await self.event_service.score(self.session, event.id)
            if scored is not None:
                result["alpha_score"] = scored.event_alpha_score
        except Exception as e:
            logger.exception("Scoring failed for event %s", event.id)
            result["errors"].append(f"scoring_error: {e}")

        # Stage 4: Generate hypothesis
        try:
            hypothesis = await self.event_service.generate_hypothesis(
                self.session, event.id
            )
            if hypothesis is not None:
                result["hypothesis_id"] = str(hypothesis.id)
        except Exception as e:
            logger.exception(
                "Hypothesis generation failed for event %s", event.id
            )
            result["errors"].append(f"hypothesis_error: {e}")

        return result