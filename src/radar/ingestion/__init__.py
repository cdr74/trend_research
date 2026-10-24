"""Signal ingestion engine and source collectors."""

from radar.ingestion.arxiv import (
    ArxivIngestor,
    parse_arxiv_atom_feed,
)
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
    "ArxivIngestor",
    "BaseIngestor",
    "EngagementTelemetry",
    "SourceCatalog",
    "SourceConfig",
    "compute_engagement_velocity",
    "load_source_catalog",
    "parse_arxiv_atom_feed",
]
