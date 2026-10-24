"""Unit tests for the Antigravity CLI (agy) LLM provider bridge."""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel

from radar.core.exceptions import ProviderError
from radar.providers.agy import AgyCliProvider
from radar.providers.base import LLMProvider


class SampleOutputModel(BaseModel):
    name: str
    score: float
    is_valid: bool


def test_agy_provider_protocol_compliance() -> None:
    # agy is installed in our test environment
    provider = AgyCliProvider()
    assert isinstance(provider, LLMProvider)


def test_agy_provider_missing_binary_raises() -> None:
    with pytest.raises(ProviderError) as exc:
        AgyCliProvider(binary_path="non_existent_binary_xyz123")
    assert "not found on system PATH" in str(exc.value)


@pytest.mark.asyncio
async def test_agy_generate_text_mocked() -> None:
    provider = AgyCliProvider()

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"Generated analysis text from agy", b"")
    mock_proc.returncode = 0

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
        result = await provider.generate_text("Analyze this tool", system_prompt="Be concise")
        assert result == "Generated analysis text from agy"
        mock_exec.assert_called_once()
        cmd = mock_exec.call_args[0]
        assert "-p" in cmd
        assert "--output-format" in cmd
        assert "text" in cmd


@pytest.mark.asyncio
async def test_agy_generate_structured_native_schema() -> None:
    provider = AgyCliProvider()

    envelope = {
        "status": "SUCCESS",
        "structured_output": {
            "name": "Playwright",
            "score": 0.95,
            "is_valid": True,
        },
        "response": '{"name": "Playwright", "score": 0.95, "is_valid": true}',
    }

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (json.dumps(envelope).encode(), b"")
    mock_proc.returncode = 0

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
        res = await provider.generate_structured("Extract data", SampleOutputModel)
        assert isinstance(res, SampleOutputModel)
        assert res.name == "Playwright"
        assert res.score == 0.95
        assert res.is_valid is True

        cmd = mock_exec.call_args[0]
        assert "--json-schema" in cmd
        assert "--output-format" in cmd
        assert "json" in cmd


@pytest.mark.asyncio
async def test_agy_generate_structured_fallback_response_string() -> None:
    provider = AgyCliProvider()

    envelope = {
        "status": "SUCCESS",
        "response": '```json\n{"name": "Vitest", "score": 0.88, "is_valid": true}\n```',
    }

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (json.dumps(envelope).encode(), b"")
    mock_proc.returncode = 0

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        res = await provider.generate_structured("Extract data", SampleOutputModel)
        assert res.name == "Vitest"
        assert res.score == 0.88


@pytest.mark.asyncio
async def test_agy_subprocess_failure_raises_provider_error() -> None:
    provider = AgyCliProvider()

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"", b"Authentication failed. Please login.")
    mock_proc.returncode = 1

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        with pytest.raises(ProviderError) as exc:
            await provider.generate_text("Prompt")
        assert "Authentication failed" in str(exc.value)


@pytest.mark.asyncio
async def test_agy_subprocess_timeout_raises_provider_error() -> None:
    provider = AgyCliProvider(timeout=0.01)

    async def slow_communicate() -> tuple[bytes, bytes]:
        await asyncio.sleep(0.1)
        return b"", b""

    mock_proc = AsyncMock()
    mock_proc.communicate = slow_communicate

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        with pytest.raises(ProviderError) as exc:
            await provider.generate_text("Prompt")
        assert "timed out" in str(exc.value)


@pytest.mark.asyncio
async def test_agy_embed_text() -> None:
    provider = AgyCliProvider()
    vec = await provider.embed_text("Sample input text")
    assert len(vec) == 1536
    assert all(isinstance(v, float) for v in vec)
