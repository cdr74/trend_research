"""Unit tests for the HackerNews / Algolia community discussion collector."""

from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from radar.core.models import SourceType
from radar.ingestion.base import BaseIngestor
from radar.ingestion.community import (
    HnAlgoliaIngestor,
    parse_hn_story_item,
)

SAMPLE_HN_HIT_1: dict[str, Any] = {
    "objectID": "1001",
    "title": "Show HN: Simantic – Firmware Simulation for AI Agents",
    "url": "https://example.com/simantic",
    "author": "simantic_founder",
    "points": 69,
    "num_comments": 21,
    "story_text": "We built a simulator for embedded agent testing in headless CI.",
    "created_at": "2026-10-29T15:56:32Z",
    "created_at_i": 1793289392,
}

SAMPLE_HN_HIT_2: dict[str, Any] = {
    "objectID": "1002",
    "title": "Show HN: Find overlapping Rust tests with mutation testing",
    "url": None,  # Ask HN / Show HN text post with no external URL
    "author": "rust_dev",
    "points": 15,
    "num_comments": 8,
    "story_text": None,
    "created_at": "2026-10-25T10:00:00Z",
    "created_at_i": 1792922400,
}

SAMPLE_HN_RESPONSE: dict[str, Any] = {
    "hits": [SAMPLE_HN_HIT_1, SAMPLE_HN_HIT_2],
    "nbHits": 2,
    "page": 0,
    "hitsPerPage": 20,
}


def test_hn_ingestor_protocol_compliance() -> None:
    ingestor = HnAlgoliaIngestor()
    assert isinstance(ingestor, BaseIngestor)
    assert ingestor.name == "community"
    assert ingestor.source_type == SourceType.COMMUNITY
    assert ingestor.source_authority_weight == 0.85


def test_parse_hn_story_item_with_external_url() -> None:
    payload = parse_hn_story_item(SAMPLE_HN_HIT_1, authority_weight=0.85)
    assert payload is not None
    assert payload.source_type == SourceType.COMMUNITY
    assert payload.source_url == "https://example.com/simantic"
    assert payload.title == "Show HN: Simantic – Firmware Simulation for AI Agents"
    assert "embedded agent testing" in payload.raw_content
    assert payload.author == "simantic_founder"
    assert payload.published_date == datetime(2026, 10, 29, 15, 56, 32, tzinfo=UTC)

    # Telemetry and engagement
    assert payload.engagement_metrics["points"] == 69.0
    assert payload.engagement_metrics["comments"] == 21.0
    assert payload.engagement_metrics["velocity"] > 0.0

    # Metadata
    assert payload.metadata["object_id"] == "1001"
    assert payload.metadata["hn_item_url"] == "https://news.ycombinator.com/item?id=1001"


def test_parse_hn_story_item_without_external_url() -> None:
    payload = parse_hn_story_item(SAMPLE_HN_HIT_2, authority_weight=0.85)
    assert payload is not None
    # Falls back to discussion URL
    assert payload.source_url == "https://news.ycombinator.com/item?id=1002"
    assert payload.title == "Show HN: Find overlapping Rust tests with mutation testing"
    assert payload.author == "rust_dev"
    assert payload.engagement_metrics["points"] == 15.0


def test_parse_hn_story_item_missing_title() -> None:
    bad_item: dict[str, Any] = {"objectID": "999", "title": None}
    assert parse_hn_story_item(bad_item) is None


@pytest.mark.asyncio
async def test_hn_ingestor_fetch_records_with_mock_transport() -> None:
    requested_queries: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_queries.append(request.url.params.get("query", ""))
        return httpx.Response(200, json=SAMPLE_HN_RESPONSE)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = HnAlgoliaIngestor(
            client=client,
            search_query="mutation testing OR test generation",
            rate_limit_delay=0.0,
        )
        records = [r async for r in ingestor.fetch_records(limit=2)]
        assert len(records) == 2
        assert records[0].title == "Show HN: Simantic – Firmware Simulation for AI Agents"
        # First query was executed
        assert requested_queries[0] == "mutation testing"


@pytest.mark.asyncio
async def test_hn_ingestor_since_filtering() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(200, json=SAMPLE_HN_RESPONSE)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = HnAlgoliaIngestor(
            client=client,
            search_query="mutation testing",
            rate_limit_delay=0.0,
        )
        # Cutoff: 2026-10-27. Hit 1 (2026-10-29) passes, Hit 2 (2026-10-25) is omitted
        since_cutoff = datetime(2026, 10, 27, 0, 0, 0, tzinfo=UTC)
        records = [r async for r in ingestor.fetch_records(since=since_cutoff, limit=10)]
        assert len(records) == 1
        assert records[0].metadata["object_id"] == "1001"


@pytest.mark.asyncio
async def test_hn_ingestor_check_health() -> None:
    def healthy_handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(200, json={"hits": []})

    transport = httpx.MockTransport(healthy_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = HnAlgoliaIngestor(client=client, rate_limit_delay=0.0)
        assert await ingestor.check_health() is True

    def fail_handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(500, json={"message": "Internal error"})

    fail_transport = httpx.MockTransport(fail_handler)
    async with httpx.AsyncClient(transport=fail_transport) as fail_client:
        failing_ingestor = HnAlgoliaIngestor(client=fail_client, rate_limit_delay=0.0)
        assert await failing_ingestor.check_health() is False
