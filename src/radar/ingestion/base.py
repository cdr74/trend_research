"""Base ingestion contracts and engagement telemetry normalizer."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

from radar.core.models import SourcePayload, SourceType


class EngagementTelemetry(BaseModel):
    """Normalized engagement metrics across heterogeneous sources."""

    stars: int | None = Field(default=None, description="GitHub repository stars")
    forks: int | None = Field(default=None, description="GitHub repository forks")
    citations: int | None = Field(default=None, description="Academic paper citation count")
    downloads: int | None = Field(default=None, description="Package / paper download count")
    views: int | None = Field(default=None, description="Article / video view count")
    discussions: int | None = Field(default=None, description="Comment or discussion thread count")

    def to_dict(self) -> dict[str, float]:
        """Convert populated metrics into a normalized float dictionary."""
        metrics: dict[str, float] = {}
        for key in ("stars", "forks", "citations", "downloads", "views", "discussions"):
            val = getattr(self, key)
            if val is not None:
                metrics[key] = float(val)
        return metrics


def compute_engagement_velocity(
    telemetry: EngagementTelemetry | dict[str, float],
    published_date: datetime | None = None,
    reference_date: datetime | None = None,
    source_authority_weight: float = 1.0,
) -> float:
    """Calculate time-decayed audience traction velocity.

    Velocity = (Weighted Engagement Points / Delta Days) * Source Authority Weight

    Weights:
        - Citations: 10.0x
        - Forks: 2.0x
        - Stars: 1.0x
        - Discussions: 0.5x
        - Downloads: 0.1x
        - Views: 0.01x
    """
    metrics = telemetry.to_dict() if isinstance(telemetry, EngagementTelemetry) else telemetry
    if not metrics:
        return 0.0

    ref = reference_date or datetime.now(UTC)

    if published_date is not None:
        delta_seconds = (ref - published_date).total_seconds()
        # Floor to at least 1 day (86400 seconds) to avoid division explosions on fresh items
        delta_days = max(1.0, delta_seconds / 86400.0)
    else:
        # Default fallback age of 7 days if published date is unknown
        delta_days = 7.0

    weights = {
        "citations": 10.0,
        "forks": 2.0,
        "stars": 1.0,
        "discussions": 0.5,
        "downloads": 0.1,
        "views": 0.01,
    }

    raw_points = 0.0
    for metric_name, weight in weights.items():
        if metric_name in metrics:
            raw_points += metrics[metric_name] * weight

    daily_velocity = raw_points / delta_days
    final_velocity = daily_velocity * source_authority_weight

    return round(final_velocity, 2)


@runtime_checkable
class BaseIngestor(Protocol):
    """Asynchronous protocol for all source channel collectors."""

    name: str
    source_type: SourceType
    source_authority_weight: float

    def fetch_records(
        self,
        since: datetime | None = None,
        limit: int = 50,
    ) -> AsyncGenerator[SourcePayload, None]:
        """Fetch and yield normalized SourcePayload instances."""
        ...

    async def check_health(self) -> bool:
        """Verify collector credentials and upstream endpoint availability."""
        ...
