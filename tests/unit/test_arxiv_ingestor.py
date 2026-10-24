"""Unit tests for the arXiv academic pre-print ingestion collector."""

import xml.etree.ElementTree as ET
from datetime import UTC, datetime

import httpx
import pytest

from radar.core.models import SourceType
from radar.ingestion.arxiv import (
    ArxivIngestor,
    _clean_text,
    _format_authors,
    _parse_arxiv_id,
    parse_arxiv_atom_feed,
)
from radar.ingestion.base import BaseIngestor

SAMPLE_ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <link href="http://arxiv.org/api/query?search_query=cat%3Acs.SE&amp;id_list=&amp;start=0&amp;max_results=2" rel="self" type="application/atom+xml"/>
  <title type="html">ArXiv Query: search_query=cat:cs.SE</title>
  <id>http://arxiv.org/api/xyz123</id>
  <updated>2026-10-23T12:00:00Z</updated>
  <entry>
    <id>http://arxiv.org/abs/2410.18021v2</id>
    <updated>2026-10-22T17:49:15Z</updated>
    <published>2026-10-20T10:00:00Z</published>
    <title>
      Automated Mutation Testing
      for Autonomous Driving Systems
    </title>
    <summary>
      Mutation testing has emerged as a gold standard for assessing test suite
      quality. In this paper, we propose an automated mutation framework.
    </summary>
    <author>
      <name>Alice Smith</name>
    </author>
    <author>
      <name>Bob Jones</name>
    </author>
    <arxiv:doi>10.1145/1234567.890</arxiv:doi>
    <arxiv:comment>Accepted to ICSE 2026, 12 pages, 4 figures</arxiv:comment>
    <arxiv:journal_ref>ACM Transactions on Software Engineering 2026</arxiv:journal_ref>
    <link href="http://arxiv.org/abs/2410.18021v2" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2410.18021v2" rel="related" type="application/pdf"/>
    <arxiv:primary_category term="cs.SE" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.SE" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2410.19999v1</id>
    <updated>2026-10-18T08:00:00Z</updated>
    <published>2026-10-18T08:00:00Z</published>
    <title>Property-Based Fuzzing of Smart Contracts</title>
    <summary>We present a novel property-based fuzzing engine for Solidity contracts.</summary>
    <author>
      <name>Charlie Brown</name>
    </author>
    <author>
      <name>David Lee</name>
    </author>
    <author>
      <name>Elena Rostova</name>
    </author>
    <link href="http://arxiv.org/abs/2410.19999v1" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2410.19999v1" rel="related" type="application/pdf"/>
    <arxiv:primary_category term="cs.CR" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.CR" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.SE" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
</feed>
"""


def test_arxiv_ingestor_protocol_compliance() -> None:
    ingestor = ArxivIngestor()
    assert isinstance(ingestor, BaseIngestor)
    assert ingestor.name == "arxiv"
    assert ingestor.source_type == SourceType.ARXIV
    assert ingestor.source_authority_weight == 1.3


def test_parse_arxiv_atom_feed_valid_xml() -> None:
    records = parse_arxiv_atom_feed(SAMPLE_ARXIV_XML, authority_weight=1.3)
    assert len(records) == 2

    first = records[0]
    assert first.source_type == SourceType.ARXIV
    assert first.source_url == "http://arxiv.org/abs/2410.18021v2"
    assert first.title == "Automated Mutation Testing for Autonomous Driving Systems"
    assert (
        first.raw_content
        == "Mutation testing has emerged as a gold standard for assessing test suite quality. In this paper, we propose an automated mutation framework."
    )
    assert first.author == "Alice Smith & Bob Jones"
    assert first.published_date == datetime(2026, 10, 20, 10, 0, 0, tzinfo=UTC)

    # Metadata assertions
    assert first.metadata["arxiv_id"] == "2410.18021"
    assert first.metadata["version"] == "v2"
    assert first.metadata["primary_category"] == "cs.SE"
    assert first.metadata["categories"] == ["cs.SE", "cs.AI"]
    assert first.metadata["authors"] == ["Alice Smith", "Bob Jones"]
    assert first.metadata["pdf_url"] == "http://arxiv.org/pdf/2410.18021v2"
    assert first.metadata["doi"] == "10.1145/1234567.890"
    assert first.metadata["comment"] == "Accepted to ICSE 2026, 12 pages, 4 figures"
    assert first.metadata["journal_ref"] == "ACM Transactions on Software Engineering 2026"

    # Second entry checks (3+ authors should format as Lead Author et al.)
    second = records[1]
    assert second.author == "Charlie Brown et al."
    assert second.metadata["arxiv_id"] == "2410.19999"
    assert second.metadata["version"] == "v1"
    assert second.metadata["primary_category"] == "cs.CR"
    assert second.metadata["categories"] == ["cs.CR", "cs.SE"]


def test_parse_arxiv_atom_feed_empty() -> None:
    empty_feed = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <title>Empty Feed</title>
    </feed>
    """
    records = parse_arxiv_atom_feed(empty_feed)
    assert len(records) == 0


def test_parse_arxiv_atom_feed_malformed() -> None:
    with pytest.raises(ET.ParseError):
        parse_arxiv_atom_feed("<feed><unclosed_tag></feed>")


@pytest.mark.asyncio
async def test_arxiv_ingestor_fetch_records_with_mock_transport() -> None:
    requested_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        return httpx.Response(200, text=SAMPLE_ARXIV_XML)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = ArxivIngestor(
            client=client,
            search_query="cat:cs.SE",
            rate_limit_delay=0.0,  # Zero delay for unit tests
        )

        records = [r async for r in ingestor.fetch_records(limit=2)]
        assert len(records) == 2
        assert records[0].title == "Automated Mutation Testing for Autonomous Driving Systems"
        assert len(requested_urls) == 1
        assert "cat%3Acs.SE" in requested_urls[0] or "cat:cs.SE" in requested_urls[0]


@pytest.mark.asyncio
async def test_arxiv_ingestor_fetch_records_since_filtering() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(200, text=SAMPLE_ARXIV_XML)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = ArxivIngestor(
            client=client,
            rate_limit_delay=0.0,
        )

        # Filter signals published after 2026-10-19: only entry 1 should be yielded (published 2026-10-20)
        since_cutoff = datetime(2026, 10, 19, 0, 0, 0, tzinfo=UTC)
        records = [r async for r in ingestor.fetch_records(since=since_cutoff, limit=10)]
        assert len(records) == 1
        assert records[0].metadata["arxiv_id"] == "2410.18021"


@pytest.mark.asyncio
async def test_arxiv_ingestor_check_health_healthy() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(200, text=SAMPLE_ARXIV_XML)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = ArxivIngestor(client=client, rate_limit_delay=0.0)
        healthy = await ingestor.check_health()
        assert healthy is True


@pytest.mark.asyncio
async def test_arxiv_ingestor_check_health_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(503, text="Service Unavailable")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = ArxivIngestor(client=client, rate_limit_delay=0.0)
        healthy = await ingestor.check_health()
        assert healthy is False


@pytest.mark.asyncio
async def test_arxiv_ingestor_retry_on_transient_error() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        _ = request
        if attempts == 1:
            return httpx.Response(429, text="Rate limit exceeded")
        return httpx.Response(200, text=SAMPLE_ARXIV_XML)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = ArxivIngestor(
            client=client,
            rate_limit_delay=0.0,
            retry_backoff_base=0.01,  # Fast backoff for tests
        )
        records = [r async for r in ingestor.fetch_records(limit=2)]
        assert len(records) == 2
        assert attempts == 2


def test_helper_clean_text_and_author_formatting() -> None:
    assert _clean_text(None) == ""
    assert _clean_text("") == ""
    assert _clean_text("  hello   world \n test  ") == "hello world test"

    assert _format_authors([]) is None
    assert _format_authors(["Single Author"]) == "Single Author"
    assert _format_authors(["Author A", "Author B"]) == "Author A & Author B"
    assert _format_authors(["A", "B", "C"]) == "A et al."


def test_parse_arxiv_id_variations() -> None:
    bare, ver = _parse_arxiv_id("http://arxiv.org/abs/2410.12345v3")
    assert bare == "2410.12345"
    assert ver == "v3"

    bare_no_ver, ver_no_ver = _parse_arxiv_id("2410.12345")
    assert bare_no_ver == "2410.12345"
    assert ver_no_ver == "v1"

    empty_bare, empty_ver = _parse_arxiv_id("")
    assert empty_bare == ""
    assert empty_ver == "v1"


@pytest.mark.asyncio
async def test_arxiv_ingestor_throttling() -> None:
    ingestor = ArxivIngestor(rate_limit_delay=0.02)
    start = datetime.now(UTC)
    await ingestor._throttle()
    await ingestor._throttle()
    duration = (datetime.now(UTC) - start).total_seconds()
    assert duration >= 0.015


@pytest.mark.asyncio
async def test_arxiv_ingestor_pagination_and_empty_break() -> None:
    page_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        nonlocal page_count
        page_count += 1
        # Page 1 returns 2 entries, page 2 returns empty feed
        if page_count == 1:
            return httpx.Response(200, text=SAMPLE_ARXIV_XML)
        return httpx.Response(200, text="<feed xmlns='http://www.w3.org/2005/Atom'></feed>")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = ArxivIngestor(client=client, rate_limit_delay=0.0, page_size=2)
        records = [r async for r in ingestor.fetch_records(limit=3)]
        assert len(records) == 2
        assert page_count == 2


@pytest.mark.asyncio
async def test_arxiv_ingestor_check_health_network_exception() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        raise httpx.ConnectError("Network is unreachable")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = ArxivIngestor(client=client, rate_limit_delay=0.0)
        healthy = await ingestor.check_health()
        assert healthy is False


@pytest.mark.asyncio
async def test_arxiv_ingestor_max_retries_exceeded() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(500, text="Internal Server Error")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = ArxivIngestor(
            client=client,
            rate_limit_delay=0.0,
            max_retries=1,
            retry_backoff_base=0.01,
        )
        with pytest.raises(httpx.HTTPStatusError):
            _ = [r async for r in ingestor.fetch_records(limit=2)]


@pytest.mark.asyncio
async def test_arxiv_ingestor_owns_client_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(200, text=SAMPLE_ARXIV_XML)

    transport = httpx.MockTransport(handler)
    real_async_client = httpx.AsyncClient

    def mock_client_factory(*_args: object, **kwargs: object) -> httpx.AsyncClient:
        kwargs["transport"] = transport
        return real_async_client(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(httpx, "AsyncClient", mock_client_factory)

    ingestor = ArxivIngestor(client=None, rate_limit_delay=0.0)
    records = [r async for r in ingestor.fetch_records(limit=1)]
    assert len(records) == 1

    healthy = await ingestor.check_health()
    assert healthy is True
