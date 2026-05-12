import hashlib
import json
import logging
import time
from typing import Optional

import httpx

from app.core.config import settings
from app.llm.base import BaseLLMProvider
from app.schemas.llm_outputs import (
    AssetMappingOutput,
    ExtractedEventOutput,
    HypothesisOutput,
)

logger = logging.getLogger(__name__)


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek LLM provider.

    NOTE: This is a stub implementation. Set DEEPSEEK_API_KEY in your environment
    or .env file to enable actual API calls.
    """

    def __init__(
        self,
        model_name: str = "deepseek-chat",
        api_key: str | None = None,
        base_url: str = "https://api.deepseek.com/v1",
    ) -> None:
        super().__init__(model_name)
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.base_url = base_url
        if not self.api_key:
            logger.warning(
                "DEEPSEEK_API_KEY is not set. DeepSeekProvider will raise "
                "NotImplementedError until a valid API key is configured."
            )

    async def _call_api(
        self,
        messages: list[dict],
        response_schema: dict | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> dict:
        """Call the DeepSeek API via OpenAI-compatible endpoint.

        Raises NotImplementedError until DEEPSEEK_API_KEY is configured.
        """
        if not self.api_key:
            raise NotImplementedError(
                "DEEPSEEK_API_KEY is not configured. Set the environment variable "
                "DEEPSEEK_API_KEY or add it to your .env file to use the DeepSeek provider. "
                "Alternatively, set LLM_PROVIDER=mock or MOCK_LLM_ENABLED=True to use "
                "the mock provider."
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: dict = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)

    async def extract_event(
        self, title: str, content: str, source: str, published_at: str
    ) -> ExtractedEventOutput:
        raise NotImplementedError(
            "DEEPSEEK_API_KEY is not configured. Set the environment variable "
            "DEEPSEEK_API_KEY or add it to your .env file to use the DeepSeek provider. "
            "Alternatively, set LLM_PROVIDER=mock or MOCK_LLM_ENABLED=True."
        )

    async def map_event_to_assets(
        self,
        event_summary: str,
        event_type: str,
        primary_entity: str,
        assets: list[dict],
    ) -> AssetMappingOutput:
        raise NotImplementedError(
            "DEEPSEEK_API_KEY is not configured. Set the environment variable "
            "DEEPSEEK_API_KEY or add it to your .env file to use the DeepSeek provider. "
            "Alternatively, set LLM_PROVIDER=mock or MOCK_LLM_ENABLED=True."
        )

    async def generate_hypothesis(
        self,
        event_summary: str,
        event_type: str,
        linked_assets: list[dict],
    ) -> HypothesisOutput:
        raise NotImplementedError(
            "DEEPSEEK_API_KEY is not configured. Set the environment variable "
            "DEEPSEEK_API_KEY or add it to your .env file to use the DeepSeek provider. "
            "Alternatively, set LLM_PROVIDER=mock or MOCK_LLM_ENABLED=True."
        )