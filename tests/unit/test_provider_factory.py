"""Unit tests for the LLM provider factory."""

import shutil

import pytest

from radar.core.config import LLMProviderType, settings
from radar.core.exceptions import ProviderError
from radar.providers import (
    AgyCliProvider,
    GeminiProvider,
    MockProvider,
    OpenAICompatProvider,
    get_llm_provider,
)


def test_get_llm_provider_mock() -> None:
    provider = get_llm_provider(LLMProviderType.MOCK)
    assert isinstance(provider, MockProvider)


def test_get_llm_provider_agy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda *_args, **_kwargs: "/usr/local/bin/agy")
    provider = get_llm_provider(LLMProviderType.AGY)
    assert isinstance(provider, AgyCliProvider)


def test_get_llm_provider_openai_compat() -> None:
    provider = get_llm_provider(LLMProviderType.OPENAI_COMPAT)
    assert isinstance(provider, OpenAICompatProvider)


def test_get_llm_provider_ollama() -> None:
    provider = get_llm_provider(LLMProviderType.OLLAMA)
    assert isinstance(provider, OpenAICompatProvider)


def test_get_llm_provider_gemini(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "gemini_api_key", "mock_key")
    provider = get_llm_provider(LLMProviderType.GEMINI)
    assert isinstance(provider, GeminiProvider)


def test_get_llm_provider_unsupported() -> None:
    with pytest.raises(ProviderError):
        get_llm_provider("unsupported_type")  # type: ignore[arg-type]
