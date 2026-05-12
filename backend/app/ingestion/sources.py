from abc import ABC, abstractmethod

from app.db.seed import SEED_DOCUMENTS


class BaseIngestionSource(ABC):
    """Abstract base for all ingestion sources."""

    @abstractmethod
    async def fetch(self) -> list[dict]:
        """Fetch documents from the source.

        Returns a list of dicts, each representing a document with fields
        matching the RawDocument model.
        """
        ...


class DemoIngestionSource(BaseIngestionSource):
    """Returns the 8 built-in seed documents for demo/testing purposes."""

    async def fetch(self) -> list[dict]:
        return list(SEED_DOCUMENTS)