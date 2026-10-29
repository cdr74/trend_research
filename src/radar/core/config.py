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
    AGY = "agy"


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
    gemini_model_name: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL_NAME")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="http://localhost:11434/v1",
        alias="OPENAI_BASE_URL",
    )
    openai_model_name: str = Field(
        default="llama3.2",
        alias="OPENAI_MODEL_NAME",
    )
    agy_binary_path: str = Field(default="agy", alias="AGY_BINARY_PATH")
    agy_model_name: str | None = Field(default=None, alias="AGY_MODEL_NAME")
    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")

    # Pipeline defaults
    batch_size: int = Field(default=20, alias="RADAR_BATCH_SIZE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Topic Convergence & Wrapper Detection (Stage 3 / Option 3B)
    topic_convergence_threshold: float = Field(
        default=0.82,
        ge=0.0,
        le=1.0,
        alias="RADAR_TOPIC_CONVERGENCE_THRESHOLD",
        description="Minimum cosine similarity threshold to merge dossiers into an existing TrendTopic",
    )
    wrapper_similarity_threshold: float = Field(
        default=0.88,
        ge=0.0,
        le=1.0,
        alias="RADAR_WRAPPER_SIMILARITY_THRESHOLD",
        description="Cosine similarity threshold above which a dossier is scrutinized for parasitic wrapper detection",
    )
    wrapper_penalty: float = Field(
        default=0.20,
        ge=0.0,
        le=1.0,
        alias="RADAR_WRAPPER_PENALTY",
        description="Score deduction applied to detected parasitic wrappers",
    )
    corroboration_consensus_bonus: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        alias="RADAR_CORROBORATION_CONSENSUS_BONUS",
        description="Validity bonus awarded when a topic reaches >= 3 distinct source channels",
    )

    # Multi-Lens Adversarial Committee Weights (Stage 3 / Option 2C)
    security_weight: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        alias="RADAR_SECURITY_WEIGHT",
        description="Evaluation weight for Security & Data Privacy lens",
    )
    cicd_weight: float = Field(
        default=0.35,
        ge=0.0,
        le=1.0,
        alias="RADAR_CICD_WEIGHT",
        description="Evaluation weight for Operational Feasibility & CI/CD lens",
    )
    qe_weight: float = Field(
        default=0.30,
        ge=0.0,
        le=1.0,
        alias="RADAR_QE_WEIGHT",
        description="Evaluation weight for Technical Rigor & Empirical Problem Solving lens",
    )

    # Radar Ring Thresholds (Stage 4)
    ring_adopt_min_viability: float = Field(
        default=0.80, ge=0.0, le=1.0, alias="RADAR_RING_ADOPT_MIN_VIABILITY"
    )
    ring_adopt_max_hype: float = Field(
        default=0.30, ge=0.0, le=1.0, alias="RADAR_RING_ADOPT_MAX_HYPE"
    )
    ring_trial_min_viability: float = Field(
        default=0.70, ge=0.0, le=1.0, alias="RADAR_RING_TRIAL_MIN_VIABILITY"
    )
    ring_trial_max_hype: float = Field(
        default=0.40, ge=0.0, le=1.0, alias="RADAR_RING_TRIAL_MAX_HYPE"
    )
    ring_assess_min_viability: float = Field(
        default=0.45, ge=0.0, le=1.0, alias="RADAR_RING_ASSESS_MIN_VIABILITY"
    )
    stars_consolidated_threshold: float = Field(
        default=500.0, ge=0.0, alias="RADAR_STARS_CONSOLIDATED_THRESHOLD"
    )
    velocity_emerging_threshold: float = Field(
        default=25.0, ge=0.0, alias="RADAR_VELOCITY_EMERGING_THRESHOLD"
    )
    velocity_fading_threshold: float = Field(
        default=5.0, ge=0.0, alias="RADAR_VELOCITY_FADING_THRESHOLD"
    )

    # Data paths
    export_dir: Path = Field(default=Path("data/export"))
    reports_dir: Path = Field(default=Path("reports"))


settings = Settings()
