"""Google Gemini LLM and Embedding provider adapter."""

from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from radar.core.config import settings
from radar.core.exceptions import ProviderError
from radar.providers.base import LLMProvider
from radar.providers.utils import build_schema_prompt, parse_and_validate

T = TypeVar("T", bound=BaseModel)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(LLMProvider):
    """Provider adapter interfacing with Google Gemini models via REST."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        timeout: float = 60.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key or settings.gemini_api_key
        if not self.api_key:
            raise ProviderError("GEMINI_API_KEY must be provided for GeminiProvider.")
        self.model_name = model_name or settings.gemini_model_name
        self.timeout = timeout
        self._client = client

    async def _post(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        url = f"{GEMINI_API_BASE}/{endpoint}?key={self.api_key}"
        try:
            resp = await client.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, dict):
                raise ProviderError(f"Unexpected response from Gemini: {data}")
            return data
        except httpx.HTTPStatusError as err:
            raise ProviderError(
                f"Gemini API request failed with status {err.response.status_code}: {err.response.text}"
            ) from err
        except httpx.RequestError as err:
            raise ProviderError(f"Gemini API request failed: {err}") from err

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate unstructured text from Gemini."""
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
        }
        if system_prompt:
            payload["system_instruction"] = {"parts": [{"text": system_prompt}]}

        owns_client = self._client is None
        client = (
            self._client if self._client is not None else httpx.AsyncClient(timeout=self.timeout)
        )
        try:
            data = await self._post(client, f"{self.model_name}:generateContent", payload)
            candidates = data.get("candidates") or []
            if not candidates:
                raise ProviderError(f"No candidates returned from Gemini: {data}")
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise ProviderError(f"Empty parts returned from Gemini: {data}")
            return str(parts[0].get("text", "")).strip()
        finally:
            if owns_client:
                await client.aclose()

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
    ) -> T:
        """Generate structured JSON adhering to response_model."""
        user_p, sys_p = build_schema_prompt(prompt, response_model, system_prompt)

        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": user_p}]}],
            "system_instruction": {"parts": [{"text": sys_p}]},
            "generationConfig": {"response_mime_type": "application/json"},
        }

        owns_client = self._client is None
        client = (
            self._client if self._client is not None else httpx.AsyncClient(timeout=self.timeout)
        )
        try:
            data = await self._post(client, f"{self.model_name}:generateContent", payload)
            candidates = data.get("candidates") or []
            if not candidates:
                raise ProviderError(f"No candidates returned from Gemini: {data}")
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise ProviderError(f"Empty parts returned from Gemini: {data}")
            raw_text = parts[0].get("text", "")
            return parse_and_validate(raw_text, response_model)
        finally:
            if owns_client:
                await client.aclose()

    async def embed_text(self, text: str) -> list[float]:
        """Generate text embedding vector using Gemini text-embedding-004."""
        payload: dict[str, Any] = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]},
        }

        owns_client = self._client is None
        client = (
            self._client if self._client is not None else httpx.AsyncClient(timeout=self.timeout)
        )
        try:
            data = await self._post(client, "text-embedding-004:embedContent", payload)
            values = data.get("embedding", {}).get("values", [])
            if not values:
                raise ProviderError(f"No embedding values returned from Gemini: {data}")

            # Standardize to 1536 dimensions for pgvector compatibility
            vec: list[float] = [float(v) for v in values]
            if len(vec) == 768:
                vec = vec + [0.0] * 768
            elif len(vec) < 1536:
                vec = vec + [0.0] * (1536 - len(vec))
            elif len(vec) > 1536:
                vec = vec[:1536]
            return vec
        finally:
            if owns_client:
                await client.aclose()
