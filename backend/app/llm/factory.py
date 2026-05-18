from app.core.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.deepseek_provider import DeepSeekProvider
from app.llm.gemma4_provider import Gemma4Provider
from app.llm.mock_provider import MockLLMProvider
from app.llm.qwen_provider import QwenProvider

from loguru import logger


def get_llm_provider() -> BaseLLMProvider:
    """Factory: return the configured LLM provider based on settings."""
    logger.info(
        "Configuring LLM provider: MOCK_LLM_ENABLED={}, LLM_PROVIDER={}",
        settings.MOCK_LLM_ENABLED,
        settings.LLM_PROVIDER,
    )
    if settings.MOCK_LLM_ENABLED or settings.LLM_PROVIDER == "mock":
        logger.info(
            "Using MockLLMProvider (MOCK_LLM_ENABLED={}, LLM_PROVIDER={})",
            settings.MOCK_LLM_ENABLED,
            settings.LLM_PROVIDER,
        )
        return MockLLMProvider()
    elif settings.LLM_PROVIDER == "qwen":
        if not settings.QWEN_API_KEY:
            logger.warning(
                "QWEN_API_KEY is not configured for LLM_PROVIDER=qwen; "
                "falling back to MockLLMProvider"
            )
            return MockLLMProvider()
        logger.info(
            "Using QwenProvider (model={})",
            settings.QWEN_API_KEY and "qwen-max" or "qwen-max [no key]",
        )
        return QwenProvider()
    elif settings.LLM_PROVIDER == "gemma4":
        if not settings.GEMMA4_API_KEY:
            logger.warning(
                "GEMMA4_API_KEY is not configured for LLM_PROVIDER=gemma4; "
                "falling back to MockLLMProvider"
            )
            return MockLLMProvider()
        logger.info(
            "Using Gemma4Provider (model={})",
            settings.GEMMA4_MODEL_NAME,
        )
        return Gemma4Provider()
    elif settings.LLM_PROVIDER == "deepseek":
        if not settings.DEEPSEEK_API_KEY:
            logger.warning(
                "DEEPSEEK_API_KEY is not configured for LLM_PROVIDER=deepseek; "
                "falling back to MockLLMProvider"
            )
            return MockLLMProvider()
        logger.info(
            "Using DeepSeekProvider (model={})",
            settings.DEEPSEEK_API_KEY and "deepseek-chat" or "deepseek-chat [no key]",
        )
        return DeepSeekProvider()

    logger.warning(
        "Unknown LLM_PROVIDER={}, falling back to MockLLMProvider",
        settings.LLM_PROVIDER,
    )
    return MockLLMProvider()
