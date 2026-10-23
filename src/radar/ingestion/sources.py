"""Curated source catalog configuration and loader."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from radar.core.exceptions import ConfigurationError


class SourceConfig(BaseModel):
    """Configuration for an individual ingestion source stream."""

    id: str = Field(..., description="Unique source identifier (e.g. arxiv-cs-se)")
    name: str = Field(..., description="Human-readable title")
    channel: str = Field(..., description="Channel type: academic | github | rss | community")
    endpoint_url: str = Field(..., description="Base API or RSS feed URL")
    authority_weight: float = Field(default=1.0, ge=0.1, le=2.0)
    enabled: bool = Field(default=True)
    query_params: dict[str, Any] = Field(default_factory=dict)
    telemetry_fields: list[str] = Field(default_factory=list)
    description: str = Field(default="")

    @field_validator("endpoint_url")
    @classmethod
    def validate_endpoint_url(cls, v: str) -> str:
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError(f"Endpoint URL must be a valid HTTP/HTTPS URL: {v}")
        return v


class SourceCatalog(BaseModel):
    """Collection of curated trend intelligence sources."""

    version: str = "1.0"
    description: str = ""
    sources: list[SourceConfig] = Field(default_factory=list)

    @field_validator("sources")
    @classmethod
    def validate_unique_ids(cls, sources: list[SourceConfig]) -> list[SourceConfig]:
        ids = set()
        for src in sources:
            if src.id in ids:
                raise ValueError(f"Duplicate source ID detected: {src.id}")
            ids.add(src.id)
        return sources

    def get_enabled(self, channel: str | None = None) -> list[SourceConfig]:
        """Filter sources that are enabled, optionally matching a channel."""
        return [s for s in self.sources if s.enabled and (channel is None or s.channel == channel)]


def load_source_catalog(path: Path | str | None = None) -> SourceCatalog:
    """Load and validate the YAML source catalog."""
    catalog_path = Path(path) if path is not None else Path("data/seeds/sources.yaml")
    if not catalog_path.exists():
        raise ConfigurationError(f"Source catalog not found at: {catalog_path}")

    try:
        data = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
        return SourceCatalog.model_validate(data)
    except Exception as e:
        raise ConfigurationError(f"Failed to load source catalog from {catalog_path}: {e}") from e
