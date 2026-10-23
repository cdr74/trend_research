"""Google Gemini LLM and Embedding provider adapter."""

from typing import TypeVar

from pydantic import BaseModel

from radar.core.config import settings
from radar.core.exceptions import ProviderError
from radar.providers.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class GeminiProvider(LLMProvider):
    """Provider adapter interfacing with Google Gemini models."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.gemini_api_key
        if not self.api_key:
            raise ProviderError("GEMINI_API_KEY must be provided for GeminiProvider.")

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        # Implementation will connect via google-genai client
        raise NotImplementedError("Gemini live execution will be wired in M3-T1.")

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
    ) -> T:
        raise NotImplementedError("Gemini structured output will be wired in M3-T1.")

    async def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError("Gemini embeddings will be wired in M3-T1.")
