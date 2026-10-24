"""LLM and embedding provider adapters."""

from radar.core.config import LLMProviderType, settings
from radar.core.exceptions import ProviderError
from radar.providers.agy import AgyCliProvider
from radar.providers.base import LLMProvider
from radar.providers.gemini import GeminiProvider
from radar.providers.mock import MockProvider
from radar.providers.openai_compat import OpenAICompatProvider

__all__ = [
    "AgyCliProvider",
    "GeminiProvider",
    "LLMProvider",
    "MockProvider",
    "OpenAICompatProvider",
    "get_llm_provider",
]


def get_llm_provider(provider_type: LLMProviderType | None = None) -> LLMProvider:
    """Factory to retrieve the configured LLM provider."""
    p_type = provider_type or settings.llm_provider

    if p_type == LLMProviderType.AGY:
        return AgyCliProvider()
    elif p_type == LLMProviderType.MOCK:
        return MockProvider()
    elif p_type in (LLMProviderType.OPENAI_COMPAT, LLMProviderType.OLLAMA):
        return OpenAICompatProvider()
    elif p_type == LLMProviderType.GEMINI:
        return GeminiProvider()
    else:
        raise ProviderError(f"Unsupported LLM provider type: {p_type}")
