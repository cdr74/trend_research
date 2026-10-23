"""Unit tests for the ingestion engine base protocol and telemetry normalizer."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest

from radar.core.models import SourcePayload, SourceType
from radar.ingestion.base import (
    BaseIngestor,
    EngagementTelemetry,
    compute_engagement_velocity,
)


def test_engagement_telemetry_normalization() -> None:
    telemetry = EngagementTelemetry(
        stars=150,
        forks=25,
        citations=12,
        views=4500,
        discussions=30,
    )
    metric_dict = telemetry.to_dict()
    assert metric_dict["stars"] == 150.0
    assert metric_dict["forks"] == 25.0
    assert metric_dict["citations"] == 12.0
    assert metric_dict["views"] == 4500.0
    assert metric_dict["discussions"] == 30.0


def test_compute_engagement_velocity_recent_signal() -> None:
    now = datetime.now(UTC)
    # Published 2 days ago
    published = now - timedelta(days=2)

    telemetry = EngagementTelemetry(
        stars=100,  # 100 * 1.0 = 100
        forks=10,  # 10 * 2.0 = 20
    )
    # Total points = 120 / 2 days = 60.0 / day
    # Authority weight = 1.0 -> velocity = 60.0
    velocity = compute_engagement_velocity(
        telemetry=telemetry,
        published_date=published,
        reference_date=now,
        source_authority_weight=1.0,
    )
    assert velocity == pytest.approx(60.0, rel=1e-2)


def test_compute_engagement_velocity_minimum_day_floor() -> None:
    now = datetime.now(UTC)
    # Published 2 hours ago (less than 1 day floor)
    published = now - timedelta(hours=2)

    telemetry = EngagementTelemetry(stars=50)
    velocity = compute_engagement_velocity(
        telemetry=telemetry,
        published_date=published,
        reference_date=now,
        source_authority_weight=1.2,
    )
    # Days clamped to 1.0 -> 50 * 1.2 = 60.0
    assert velocity == pytest.approx(60.0, rel=1e-2)


def test_compute_engagement_velocity_without_published_date() -> None:
    # If published date is unknown, defaults to 7 days baseline
    telemetry = EngagementTelemetry(stars=70)
    velocity = compute_engagement_velocity(
        telemetry=telemetry,
        published_date=None,
        source_authority_weight=1.0,
    )
    assert velocity == pytest.approx(10.0, rel=1e-2)


class DummyTestIngestor(BaseIngestor):
    """Concrete mock ingestor for testing protocol compliance."""

    name = "dummy_collector"
    source_type = SourceType.GITHUB
    source_authority_weight = 1.0

    async def fetch_records(
        self, since: datetime | None = None, limit: int = 50
    ) -> AsyncGenerator[SourcePayload, None]:
        _ = (since, limit)
        yield SourcePayload(
            source_type=self.source_type,
            source_url="https://github.com/example/tool",
            title="Automated Test Tool",
            raw_content="README content",
            engagement_metrics={"stars": 42.0},
        )

    async def check_health(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_base_ingestor_protocol_implementation() -> None:
    ingestor = DummyTestIngestor()
    assert isinstance(ingestor, BaseIngestor)
    assert ingestor.name == "dummy_collector"
    assert ingestor.source_type == SourceType.GITHUB

    healthy = await ingestor.check_health()
    assert healthy is True

    records = [rec async for rec in ingestor.fetch_records(limit=5)]
    assert len(records) == 1
    assert records[0].title == "Automated Test Tool"
    assert records[0].engagement_metrics["stars"] == 42.0
