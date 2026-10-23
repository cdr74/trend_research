"""Unit tests for the source catalog registry and loader."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from radar.core.exceptions import ConfigurationError
from radar.ingestion.sources import (
    SourceCatalog,
    SourceConfig,
    load_source_catalog,
)


def test_load_default_seed_catalog() -> None:
    catalog = load_source_catalog()
    assert len(catalog.sources) >= 10
    assert catalog.version == "1.0"

    # Verify key channels are represented
    channels = {s.channel for s in catalog.sources}
    assert "academic" in channels
    assert "github" in channels
    assert "rss" in channels
    assert "community" in channels

    # Verify authority weights are within bounds
    for s in catalog.sources:
        assert 0.1 <= s.authority_weight <= 2.0
        assert s.endpoint_url.startswith("http")


def test_get_enabled_filtering() -> None:
    catalog = load_source_catalog()
    academic_sources = catalog.get_enabled(channel="academic")
    assert len(academic_sources) >= 2
    for s in academic_sources:
        assert s.channel == "academic"
        assert s.enabled is True


def test_duplicate_source_id_validation() -> None:
    sources = [
        SourceConfig(
            id="duplicate-id",
            name="Source 1",
            channel="academic",
            endpoint_url="https://example.com/feed1",
        ),
        SourceConfig(
            id="duplicate-id",
            name="Source 2",
            channel="github",
            endpoint_url="https://example.com/feed2",
        ),
    ]
    with pytest.raises(ValidationError):
        SourceCatalog(sources=sources)


def test_missing_catalog_raises_configuration_error() -> None:
    with pytest.raises(ConfigurationError):
        load_source_catalog(Path("non_existent_sources.yaml"))
