"""Pluggable LLM and embedding provider interface."""

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM and embedding services."""

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate unstructured text from a prompt."""
        ...

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
    ) -> T:
        """Generate structured data parsed into a Pydantic model."""
        ...

    async def embed_text(self, text: str) -> list[float]:
        """Generate a dense vector embedding for the given text."""
        ...
