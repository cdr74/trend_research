"""Deterministic Mock LLM Provider for unit and offline tests."""

import inspect
from enum import Enum
from typing import Any, TypeVar
from uuid import uuid4

from pydantic import BaseModel

from radar.providers.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class MockProvider(LLMProvider):
    """Deterministic offline mock provider."""

    def __init__(self, embedding_dim: int = 1536) -> None:
        self.embedding_dim = embedding_dim

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        _ = system_prompt
        return f"[MOCK RESPONSE] Analysis for: {prompt[:40]}..."

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
    ) -> T:
        """Instantiate response model with dummy valid values for testing."""
        _ = (prompt, system_prompt)
        fields = response_model.model_fields
        dummy_data: dict[str, Any] = {}
        for name, field_info in fields.items():
            if field_info.is_required():
                ann = field_info.annotation
                if ann is not None and inspect.isclass(ann) and issubclass(ann, Enum):
                    dummy_data[name] = list(ann)[0]
                else:
                    annotation_str = str(ann)
                    if "float" in annotation_str:
                        dummy_data[name] = 0.75
                    elif "int" in annotation_str:
                        dummy_data[name] = 1
                    elif "str" in annotation_str:
                        dummy_data[name] = "Mock Data"
                    elif "bool" in annotation_str:
                        dummy_data[name] = True
                    elif "list" in annotation_str:
                        dummy_data[name] = []
                    elif "UUID" in annotation_str:
                        dummy_data[name] = uuid4()
                    else:
                        pass
        return response_model.model_validate(dummy_data)

    async def embed_text(self, text: str) -> list[float]:
        val = float(abs(hash(text)) % 1000) / 1000.0
        return [val] * self.embedding_dim
