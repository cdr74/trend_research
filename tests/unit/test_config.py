"""Unit tests for configuration settings."""

from radar.core.config import LLMProviderType, Settings


def test_default_settings() -> None:
    config = Settings()
    assert config.batch_size == 20
    assert "postgresql" in config.database_url
    assert config.llm_provider in list(LLMProviderType)


def test_custom_settings_override() -> None:
    config = Settings(
        RADAR_LLM_PROVIDER=LLMProviderType.MOCK,
        RADAR_BATCH_SIZE=50,
    )
    assert config.llm_provider == LLMProviderType.MOCK
    assert config.batch_size == 50
