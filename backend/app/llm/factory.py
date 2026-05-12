import logging

from app.core.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.deepseek_provider import DeepSeekProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.qwen_provider import QwenProvider

logger = logging.getLogger(__name__)


def get_llm_provider() -> BaseLLMProvider:
    """Factory: return the configured LLM provider based on settings."""
    if settings.MOCK_LLM_ENABLED or settings.LLM_PROVIDER == "mock":
        logger.info("Using MockLLMProvider (MOCK_LLM_ENABLED=%s, LLM_PROVIDER=%s)", settings.MOCK_LLM_ENABLED, settings.LLM_PROVIDER)
        return MockLLMProvider()
    elif settings.LLM_PROVIDER == "qwen":
        logger.info("Using QwenProvider (model=%s)", settings.QWEN_API_KEY and "qwen-max" or "qwen-max [no key]")
        return QwenProvider()
    elif settings.LLM_PROVIDER == "deepseek":
        logger.info("Using DeepSeekProvider (model=%s)", settings.DEEPSEEK_API_KEY and "deepseek-chat" or "deepseek-chat [no key]")
        return DeepSeekProvider()

    logger.warning(
        "Unknown LLM_PROVIDER=%s, falling back to MockLLMProvider",
        settings.LLM_PROVIDER,
    )
    return MockLLMProvider()