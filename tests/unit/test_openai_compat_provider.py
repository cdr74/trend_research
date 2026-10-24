"""Unit tests for the OpenAI-compatible LLM and Embedding provider adapter."""

import httpx
import pytest
from pydantic import BaseModel

from radar.core.exceptions import ProviderError
from radar.providers.base import LLMProvider
from radar.providers.openai_compat import OpenAICompatProvider


class DummySchema(BaseModel):
    tool_name: str
    maturity: float


def test_openai_compat_protocol_compliance() -> None:
    provider = OpenAICompatProvider()
    assert isinstance(provider, LLMProvider)


@pytest.mark.asyncio
async def test_openai_compat_generate_text() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).endswith("/chat/completions")
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "OpenAI text response", "role": "assistant"}}]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenAICompatProvider(client=client, api_key="test_key")
        res = await provider.generate_text("Prompt", system_prompt="System")
        assert res == "OpenAI text response"


@pytest.mark.asyncio
async def test_openai_compat_generate_structured() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"tool_name": "Hypothesis", "maturity": 0.9}',
                            "role": "assistant",
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenAICompatProvider(client=client)
        res = await provider.generate_structured("Analyze", DummySchema)
        assert isinstance(res, DummySchema)
        assert res.tool_name == "Hypothesis"
        assert res.maturity == 0.9


@pytest.mark.asyncio
async def test_openai_compat_generate_structured_with_repair() -> None:
    turn = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal turn
        turn += 1
        _ = request
        if turn == 1:
            # First turn returns malformed JSON
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "Not valid JSON at all"}}]},
            )
        # Second turn returns corrected JSON
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": '{"tool_name": "RepairedTool", "maturity": 0.85}'}}
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenAICompatProvider(client=client)
        res = await provider.generate_structured("Analyze", DummySchema)
        assert res.tool_name == "RepairedTool"
        assert res.maturity == 0.85
        assert turn == 2


@pytest.mark.asyncio
async def test_openai_compat_embed_text() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).endswith("/embeddings")
        return httpx.Response(
            200,
            json={"data": [{"embedding": [0.123] * 1536}]},
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenAICompatProvider(client=client)
        vec = await provider.embed_text("Sample input text")
        assert len(vec) == 1536
        assert vec[0] == 0.123


@pytest.mark.asyncio
async def test_openai_compat_http_error_raises_provider_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(500, text="Internal Server Error")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenAICompatProvider(client=client)
        with pytest.raises(ProviderError) as exc:
            await provider.generate_text("Prompt")
        assert "500" in str(exc.value)
