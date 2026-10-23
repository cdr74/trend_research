"""Pytest fixtures and configuration."""

import pytest

from radar.core.config import LLMProviderType, Settings
from radar.providers.mock import MockProvider


@pytest.fixture
def mock_settings() -> Settings:
    """Fixture providing clean default settings."""
    return Settings(
        RADAR_LLM_PROVIDER=LLMProviderType.MOCK,
        RADAR_EMBEDDING_PROVIDER=LLMProviderType.MOCK,
    )


@pytest.fixture
def mock_provider() -> MockProvider:
    """Deterministic mock LLM provider."""
    return MockProvider(embedding_dim=128)
