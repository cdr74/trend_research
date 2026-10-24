"""OpenAI-compatible LLM and Embedding provider adapter (Ollama, vLLM, OpenAI)."""

from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from radar.core.config import settings
from radar.core.exceptions import ProviderError
from radar.providers.base import LLMProvider
from radar.providers.utils import build_schema_prompt, parse_and_validate

T = TypeVar("T", bound=BaseModel)


class OpenAICompatProvider(LLMProvider):
    """Provider adapter interfacing with OpenAI-compatible endpoints."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model_name: str | None = None,
        embedding_model_name: str | None = None,
        timeout: float = 60.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = (base_url or settings.openai_base_url).rstrip("/")
        self.api_key = api_key or settings.openai_api_key or "none"
        self.model_name = model_name or settings.openai_model_name
        self.embedding_model_name = embedding_model_name or "text-embedding-3-small"
        self.timeout = timeout
        self._client = client

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key and self.api_key != "none":
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _post(
        self, client: httpx.AsyncClient, path: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            resp = await client.post(
                url, json=payload, headers=self._headers(), timeout=self.timeout
            )
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, dict):
                raise ProviderError(f"Unexpected response format from {url}: {data}")
            return data
        except httpx.HTTPStatusError as err:
            raise ProviderError(
                f"OpenAI-compatible request to {url} failed with status {err.response.status_code}: {err.response.text}"
            ) from err
        except httpx.RequestError as err:
            raise ProviderError(f"OpenAI-compatible request to {url} failed: {err}") from err

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate unstructured text from prompt."""
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
        }

        owns_client = self._client is None
        client = (
            self._client if self._client is not None else httpx.AsyncClient(timeout=self.timeout)
        )
        try:
            data = await self._post(client, "/chat/completions", payload)
            choices = data.get("choices") or []
            if not choices:
                raise ProviderError(f"No choices returned from LLM: {data}")
            content = choices[0].get("message", {}).get("content", "")
            return str(content).strip()
        finally:
            if owns_client:
                await client.aclose()

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
    ) -> T:
        """Generate structured data parsed into a Pydantic model with 1-attempt repair fallback."""
        user_p, sys_p = build_schema_prompt(prompt, response_model, system_prompt)

        messages = [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": user_p},
        ]

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "response_format": {"type": "json_object"},
        }

        owns_client = self._client is None
        client = (
            self._client if self._client is not None else httpx.AsyncClient(timeout=self.timeout)
        )
        try:
            data = await self._post(client, "/chat/completions", payload)
            choices = data.get("choices") or []
            if not choices:
                raise ProviderError(f"No choices returned from LLM: {data}")
            raw_text = choices[0].get("message", {}).get("content", "")

            try:
                return parse_and_validate(raw_text, response_model)
            except ProviderError as initial_err:
                # 1-attempt repair re-prompt for local SLMs
                repair_messages = list(messages)
                repair_messages.append({"role": "assistant", "content": raw_text})
                repair_messages.append(
                    {
                        "role": "user",
                        "content": f"The previous output failed validation: {initial_err}. "
                        "Respond ONLY with a valid, corrected JSON object conforming strictly to the schema.",
                    }
                )
                repair_payload = {
                    "model": self.model_name,
                    "messages": repair_messages,
                    "response_format": {"type": "json_object"},
                }
                repair_data = await self._post(client, "/chat/completions", repair_payload)
                repair_text = (
                    (repair_data.get("choices") or [{}])[0].get("message", {}).get("content", "")
                )
                return parse_and_validate(repair_text, response_model)
        finally:
            if owns_client:
                await client.aclose()

    async def embed_text(self, text: str) -> list[float]:
        """Generate dense vector embeddings using OpenAI-compatible embeddings endpoint."""
        payload: dict[str, Any] = {
            "model": self.embedding_model_name,
            "input": text,
        }

        owns_client = self._client is None
        client = (
            self._client if self._client is not None else httpx.AsyncClient(timeout=self.timeout)
        )
        try:
            data = await self._post(client, "/embeddings", payload)
            emb_list = data.get("data") or []
            if not emb_list or "embedding" not in emb_list[0]:
                raise ProviderError(f"No embedding returned from endpoint: {data}")
            vec: list[float] = [float(x) for x in emb_list[0]["embedding"]]
            return vec
        finally:
            if owns_client:
                await client.aclose()
