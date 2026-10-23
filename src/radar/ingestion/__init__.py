"""Signal ingestion engine and source collectors."""

from radar.ingestion.base import (
    BaseIngestor,
    EngagementTelemetry,
    compute_engagement_velocity,
)
from radar.ingestion.sources import (
    SourceCatalog,
    SourceConfig,
    load_source_catalog,
)

__all__ = [
    "BaseIngestor",
    "EngagementTelemetry",
    "SourceCatalog",
    "SourceConfig",
    "compute_engagement_velocity",
    "load_source_catalog",
]
