"""Unit tests for the Google Gemini LLM and Embedding provider adapter."""

import httpx
import pytest
from pydantic import BaseModel

from radar.core.exceptions import ProviderError
from radar.providers.base import LLMProvider
from radar.providers.gemini import GeminiProvider


class GeminiDummyModel(BaseModel):
    category: str
    confidence: float


def test_gemini_missing_api_key_raises() -> None:
    with pytest.raises(ProviderError) as exc:
        GeminiProvider(api_key=None)
    assert "GEMINI_API_KEY must be provided" in str(exc.value)


def test_gemini_protocol_compliance() -> None:
    provider = GeminiProvider(api_key="test_dummy_key")
    assert isinstance(provider, LLMProvider)


@pytest.mark.asyncio
async def test_gemini_generate_text() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "generateContent" in str(request.url)
        assert "key=test_dummy_key" in str(request.url)
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": "Gemini generated text analysis."}]}}
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = GeminiProvider(api_key="test_dummy_key", client=client)
        res = await provider.generate_text("Prompt", system_prompt="System")
        assert res == "Gemini generated text analysis."


@pytest.mark.asyncio
async def test_gemini_generate_structured() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": '{"category": "Test Synthesis", "confidence": 0.92}'}
                            ]
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = GeminiProvider(api_key="test_dummy_key", client=client)
        res = await provider.generate_structured("Analyze", GeminiDummyModel)
        assert isinstance(res, GeminiDummyModel)
        assert res.category == "Test Synthesis"
        assert res.confidence == 0.92


@pytest.mark.asyncio
async def test_gemini_embed_text_normalization() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "embedContent" in str(request.url)
        # Gemini text-embedding-004 returns 768 dims
        return httpx.Response(
            200,
            json={"embedding": {"values": [0.456] * 768}},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = GeminiProvider(api_key="test_dummy_key", client=client)
        vec = await provider.embed_text("Sample paper abstract")
        # Must be padded/normalized to 1536 dims for pgvector
        assert len(vec) == 1536
        assert vec[0] == 0.456
        assert vec[768] == 0.0


@pytest.mark.asyncio
async def test_gemini_http_error_raises_provider_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(403, text="Invalid API Key")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = GeminiProvider(api_key="test_dummy_key", client=client)
        with pytest.raises(ProviderError) as exc:
            await provider.generate_text("Prompt")
        assert "403" in str(exc.value)
