"""Signal ingestion engine and source collectors."""

from radar.ingestion.base import (
    BaseIngestor,
    EngagementTelemetry,
    compute_engagement_velocity,
)

__all__ = [
    "BaseIngestor",
    "EngagementTelemetry",
    "compute_engagement_velocity",
]
