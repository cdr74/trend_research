"""OpenAI-compatible LLM and Embedding provider adapter (Ollama, vLLM, OpenAI)."""

from typing import TypeVar

from pydantic import BaseModel

from radar.core.config import settings
from radar.providers.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class OpenAICompatProvider(LLMProvider):
    """Provider adapter interfacing with OpenAI-compatible endpoints."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model_name: str | None = None,
    ) -> None:
        self.base_url = base_url or settings.openai_base_url
        self.api_key = api_key or settings.openai_api_key or "none"
        self.model_name = model_name or settings.openai_model_name

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        raise NotImplementedError("OpenAI-compatible text generation will be wired in M3-T1.")

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
    ) -> T:
        raise NotImplementedError("OpenAI-compatible structured generation will be wired in M3-T1.")

    async def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError("OpenAI-compatible embeddings will be wired in M3-T1.")
