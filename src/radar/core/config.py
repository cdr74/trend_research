"""Application and pipeline configuration settings."""

from enum import StrEnum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProviderType(StrEnum):
    """Supported LLM provider types."""

    MOCK = "mock"
    GEMINI = "gemini"
    OPENAI_COMPAT = "openai_compat"
    OLLAMA = "ollama"


class Settings(BaseSettings):
    """Radar system configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Persistence
    database_url: str = Field(
        default="postgresql+asyncpg://radar:radar_secret@localhost:5432/radar_db",
        alias="RADAR_DATABASE_URL",
    )

    # LLM & Embeddings
    llm_provider: LLMProviderType = Field(
        default=LLMProviderType.MOCK,
        alias="RADAR_LLM_PROVIDER",
    )
    embedding_provider: LLMProviderType = Field(
        default=LLMProviderType.MOCK,
        alias="RADAR_EMBEDDING_PROVIDER",
    )

    # Provider credentials / endpoints
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="http://localhost:11434/v1",
        alias="OPENAI_BASE_URL",
    )
    openai_model_name: str = Field(
        default="llama3.2",
        alias="OPENAI_MODEL_NAME",
    )
    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")

    # Pipeline defaults
    batch_size: int = Field(default=20, alias="RADAR_BATCH_SIZE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Data paths
    export_dir: Path = Field(default=Path("data/export"))
    reports_dir: Path = Field(default=Path("reports"))


settings = Settings()
