"""Unit tests for configuration settings."""

from radar.core.config import LLMProviderType, Settings


def test_default_settings() -> None:
    config = Settings()
    assert config.batch_size == 20
    assert "postgresql" in config.database_url
    assert config.llm_provider in list(LLMProviderType)
    assert config.topic_merge_min_similarity == 0.50


def test_custom_settings_override() -> None:
    config = Settings(
        RADAR_LLM_PROVIDER=LLMProviderType.MOCK,
        RADAR_BATCH_SIZE=50,
        RADAR_TOPIC_MERGE_MIN_SIMILARITY=0.60,
    )
    assert config.llm_provider == LLMProviderType.MOCK
    assert config.batch_size == 50
    assert config.topic_merge_min_similarity == 0.60
