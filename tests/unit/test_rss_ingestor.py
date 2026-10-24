"""Unit tests for the practitioner publication RSS/Atom feed ingestion collector."""

import xml.etree.ElementTree as ET
from datetime import UTC, datetime

import httpx
import pytest

from radar.core.models import SourceType
from radar.ingestion.base import BaseIngestor
from radar.ingestion.rss import (
    RssFeedIngestor,
    _clean_html_text,
    _parse_feed_date,
    parse_syndication_feed,
)

SAMPLE_RSS_2_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>Netflix Technology Blog</title>
    <link>https://netflixtechblog.com</link>
    <item>
      <title>Chaos Engineering in the Cloud Era</title>
      <link>https://netflixtechblog.com/chaos-engineering-cloud-era</link>
      <pubDate>Wed, 23 Oct 2026 14:00:00 GMT</pubDate>
      <dc:creator>Netflix Chaos Team</dc:creator>
      <category>Chaos Engineering</category>
      <category>Reliability</category>
      <description><![CDATA[<p>How we run continuous <b>verification</b> experiments against production clusters.</p>]]></description>
    </item>
    <item>
      <title>Building Safe Canary Deployments with Automated Verification</title>
      <link>https://netflixtechblog.com/safe-canary-deployments</link>
      <pubDate>Mon, 20 Oct 2026 10:30:00 GMT</pubDate>
      <dc:creator>John Doe</dc:creator>
      <category>Deployment</category>
      <description><![CDATA[Statistical analysis of metrics across canary and baseline clusters.]]></description>
    </item>
  </channel>
</rss>
"""

SAMPLE_ATOM_FEED_XML = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Uber Engineering Blog</title>
  <link href="https://www.uber.com/blog/engineering/"/>
  <entry>
    <title>Predictive Test Selection at Scale</title>
    <link href="https://www.uber.com/blog/predictive-test-selection/"/>
    <id>tag:uber.com,2026:predictive-tests</id>
    <published>2026-10-21T08:00:00Z</published>
    <author><name>Uber DevPlatform Team</name></author>
    <summary>Using machine learning to select relevant tests for monorepo commits.</summary>
    <category term="Testing"/>
  </entry>
</feed>
"""


def test_rss_ingestor_protocol_compliance() -> None:
    ingestor = RssFeedIngestor()
    assert isinstance(ingestor, BaseIngestor)
    assert ingestor.name == "rss"
    assert ingestor.source_type == SourceType.RSS
    assert ingestor.source_authority_weight == 1.25


def test_clean_html_text() -> None:
    assert _clean_html_text(None) == ""
    assert _clean_html_text("<p>Hello <b>World</b> &amp; Friends</p>") == "Hello World & Friends"
    assert _clean_html_text("Just plain text with spaces   ") == "Just plain text with spaces"


def test_parse_feed_date_formats() -> None:
    # RFC 2822
    rfc_date = _parse_feed_date("Wed, 23 Oct 2026 14:00:00 GMT")
    assert rfc_date == datetime(2026, 10, 23, 14, 0, 0, tzinfo=UTC)

    # ISO 8601
    iso_date = _parse_feed_date("2026-10-21T08:00:00Z")
    assert iso_date == datetime(2026, 10, 21, 8, 0, 0, tzinfo=UTC)

    # Invalid fallback
    assert _parse_feed_date("Invalid Date String") is None
    assert _parse_feed_date(None) is None


def test_parse_rss_2_feed() -> None:
    records = parse_syndication_feed(SAMPLE_RSS_2_XML, authority_weight=1.25)
    assert len(records) == 2

    first = records[0]
    assert first.source_type == SourceType.RSS
    assert first.source_url == "https://netflixtechblog.com/chaos-engineering-cloud-era"
    assert first.title == "Chaos Engineering in the Cloud Era"
    assert first.author == "Netflix Chaos Team"
    assert first.published_date == datetime(2026, 10, 23, 14, 0, 0, tzinfo=UTC)
    assert "How we run continuous verification experiments" in first.raw_content
    assert first.metadata["categories"] == ["Chaos Engineering", "Reliability"]
    assert first.engagement_metrics["velocity"] > 0.0


def test_parse_atom_feed() -> None:
    records = parse_syndication_feed(SAMPLE_ATOM_FEED_XML, authority_weight=1.25)
    assert len(records) == 1

    first = records[0]
    assert first.source_type == SourceType.RSS
    assert first.source_url == "https://www.uber.com/blog/predictive-test-selection/"
    assert first.title == "Predictive Test Selection at Scale"
    assert first.author == "Uber DevPlatform Team"
    assert first.published_date == datetime(2026, 10, 21, 8, 0, 0, tzinfo=UTC)
    assert "Using machine learning to select relevant tests" in first.raw_content
    assert first.metadata["categories"] == ["Testing"]


def test_parse_syndication_feed_keyword_filtering() -> None:
    # Only records matching keyword 'canary'
    records = parse_syndication_feed(SAMPLE_RSS_2_XML, authority_weight=1.25, keywords=["canary"])
    assert len(records) == 1
    assert "Canary Deployments" in records[0].title


def test_parse_syndication_feed_empty_or_malformed() -> None:
    with pytest.raises(ET.ParseError):
        parse_syndication_feed("<not_valid_xml>")

    empty_records = parse_syndication_feed("<unsupported></unsupported>")
    assert len(empty_records) == 0


@pytest.mark.asyncio
async def test_rss_ingestor_fetch_records_with_mock_transport() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(200, text=SAMPLE_RSS_2_XML)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = RssFeedIngestor(
            endpoint_url="https://netflixtechblog.com/feed",
            client=client,
            rate_limit_delay=0.0,
        )
        records = [r async for r in ingestor.fetch_records(limit=2)]
        assert len(records) == 2
        assert records[0].title == "Chaos Engineering in the Cloud Era"


@pytest.mark.asyncio
async def test_rss_ingestor_since_filtering() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(200, text=SAMPLE_RSS_2_XML)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = RssFeedIngestor(client=client, rate_limit_delay=0.0)
        # Cutoff: 2026-10-22. First item (Oct 23) passes, second (Oct 20) is omitted
        since_cutoff = datetime(2026, 10, 22, 0, 0, 0, tzinfo=UTC)
        records = [r async for r in ingestor.fetch_records(since=since_cutoff, limit=5)]
        assert len(records) == 1
        assert records[0].title == "Chaos Engineering in the Cloud Era"


@pytest.mark.asyncio
async def test_rss_ingestor_check_health() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(200, text=SAMPLE_RSS_2_XML)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = RssFeedIngestor(client=client, rate_limit_delay=0.0)
        assert await ingestor.check_health() is True

    def fail_handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(500, text="Internal Server Error")

    fail_transport = httpx.MockTransport(fail_handler)
    async with httpx.AsyncClient(transport=fail_transport) as fail_client:
        failing_ingestor = RssFeedIngestor(client=fail_client, rate_limit_delay=0.0)
        assert await failing_ingestor.check_health() is False
