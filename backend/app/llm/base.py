import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod

from app.schemas.llm_outputs import (
    AssetMappingOutput,
    ExtractedEventOutput,
    HypothesisOutput,
)

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base for all LLM providers."""

    def __init__(self, model_name: str = "base") -> None:
        self.model_name = model_name

    def _hash_input(self, input_data: dict) -> str:
        """Generate a deterministic SHA-256 hash for caching/deduplication."""
        return hashlib.sha256(
            json.dumps(input_data, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()

    @abstractmethod
    async def extract_event(
        self, title: str, content: str, source: str, published_at: str
    ) -> ExtractedEventOutput:
        """Extract structured event information from raw text."""
        ...

    @abstractmethod
    async def map_event_to_assets(
        self,
        event_summary: str,
        event_type: str,
        primary_entity: str,
        assets: list[dict],
    ) -> AssetMappingOutput:
        """Map an extracted event to tradable assets."""
        ...

    @abstractmethod
    async def generate_hypothesis(
        self,
        event_summary: str,
        event_type: str,
        linked_assets: list[dict],
    ) -> HypothesisOutput:
        """Generate investment hypothesis for an event-asset mapping."""
        ...