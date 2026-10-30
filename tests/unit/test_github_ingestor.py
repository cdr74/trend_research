"""Unit tests for the GitHub repository and topic ingestion collector."""

from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from radar.core.models import SourceType
from radar.ingestion.base import BaseIngestor
from radar.ingestion.github import (
    GithubIngestor,
    parse_github_repo_item,
    parse_github_search_response,
)

SAMPLE_GITHUB_ITEM_1: dict[str, Any] = {
    "id": 123456,
    "name": "playwright",
    "full_name": "microsoft/playwright",
    "html_url": "https://github.com/microsoft/playwright",
    "description": "Fast and reliable end-to-end testing for modern web apps.",
    "owner": {"login": "microsoft"},
    "stargazers_count": 65000,
    "forks_count": 3500,
    "open_issues_count": 250,
    "language": "TypeScript",
    "topics": ["testing", "browser-automation", "end-to-end-testing"],
    "license": {"spdx_id": "Apache-2.0"},
    "default_branch": "main",
    "archived": False,
    "created_at": "2020-01-15T18:00:00Z",
    "pushed_at": "2026-10-23T12:00:00Z",
}

SAMPLE_GITHUB_ITEM_2: dict[str, Any] = {
    "id": 789012,
    "name": "mutmut",
    "full_name": "boxed/mutmut",
    "html_url": "https://github.com/boxed/mutmut",
    "description": "Mutation testing system for Python 3.",
    "owner": {"login": "boxed"},
    "stargazers_count": 1200,
    "forks_count": 90,
    "open_issues_count": 30,
    "language": "Python",
    "topics": ["mutation-testing", "testing", "python"],
    "license": {"spdx_id": "BSD-3-Clause"},
    "default_branch": "master",
    "archived": False,
    "created_at": "2018-05-10T09:00:00Z",
    "pushed_at": "2026-10-10T15:00:00Z",
}

SAMPLE_GITHUB_SEARCH_RESPONSE: dict[str, Any] = {
    "total_count": 2,
    "incomplete_results": False,
    "items": [SAMPLE_GITHUB_ITEM_1, SAMPLE_GITHUB_ITEM_2],
}


def test_github_ingestor_protocol_compliance() -> None:
    ingestor = GithubIngestor()
    assert isinstance(ingestor, BaseIngestor)
    assert ingestor.name == "github"
    assert ingestor.source_type == SourceType.GITHUB
    assert ingestor.source_authority_weight == 1.1


def test_parse_github_repo_item() -> None:
    payload = parse_github_repo_item(SAMPLE_GITHUB_ITEM_1, authority_weight=1.1)

    assert payload.source_type == SourceType.GITHUB
    assert payload.source_url == "https://github.com/microsoft/playwright"
    assert payload.title == "microsoft/playwright"
    assert "Fast and reliable end-to-end testing" in payload.raw_content
    assert payload.author == "microsoft"
    assert payload.published_date == datetime(2026, 10, 23, 12, 0, 0, tzinfo=UTC)

    # Metadata checks
    assert payload.metadata["repo_name"] == "playwright"
    assert payload.metadata["owner"] == "microsoft"
    assert payload.metadata["language"] == "TypeScript"
    assert "browser-automation" in payload.metadata["topics"]
    assert payload.metadata["license"] == "Apache-2.0"

    # Engagement metrics & velocity
    assert payload.engagement_metrics["stars"] == 65000.0
    assert payload.engagement_metrics["forks"] == 3500.0
    assert payload.engagement_metrics["discussions"] == 250.0
    assert payload.engagement_metrics["velocity"] > 0.0


def test_parse_github_search_response() -> None:
    records = parse_github_search_response(SAMPLE_GITHUB_SEARCH_RESPONSE, authority_weight=1.1)
    assert len(records) == 2
    assert records[0].title == "microsoft/playwright"
    assert records[1].title == "boxed/mutmut"


@pytest.mark.asyncio
async def test_github_ingestor_fetch_records_with_mock_transport() -> None:
    requested_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        return httpx.Response(200, json=SAMPLE_GITHUB_SEARCH_RESPONSE)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = GithubIngestor(
            client=client,
            search_query="topic:test-generation sort:updated",
            rate_limit_delay=0.0,
        )
        records = [r async for r in ingestor.fetch_records(limit=2)]
        assert len(records) == 2
        assert records[0].title == "microsoft/playwright"
        assert len(requested_urls) == 1
        assert "api.github.com/search/repositories" in requested_urls[0]


@pytest.mark.asyncio
async def test_github_ingestor_token_authorization_header() -> None:
    captured_auth_header: str | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_auth_header
        captured_auth_header = request.headers.get("Authorization")
        return httpx.Response(200, json=SAMPLE_GITHUB_SEARCH_RESPONSE)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = GithubIngestor(
            client=client,
            token="ghp_test_secret_token",
            rate_limit_delay=0.0,
        )
        _ = [r async for r in ingestor.fetch_records(limit=1)]
        assert captured_auth_header == "Bearer ghp_test_secret_token"


@pytest.mark.asyncio
async def test_github_ingestor_since_filtering() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(200, json=SAMPLE_GITHUB_SEARCH_RESPONSE)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = GithubIngestor(client=client, rate_limit_delay=0.0)

        # Cutoff: 2026-10-15. Item 1 (pushed 2026-10-23) passes, Item 2 (pushed 2026-10-10) is omitted
        since_cutoff = datetime(2026, 10, 15, 0, 0, 0, tzinfo=UTC)
        records = [r async for r in ingestor.fetch_records(since=since_cutoff, limit=10)]
        assert len(records) == 1
        assert records[0].title == "microsoft/playwright"


@pytest.mark.asyncio
async def test_github_ingestor_check_health() -> None:
    def healthy_handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(200, json=SAMPLE_GITHUB_SEARCH_RESPONSE)

    transport = httpx.MockTransport(healthy_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = GithubIngestor(client=client, rate_limit_delay=0.0)
        assert await ingestor.check_health() is True

    def fail_handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(403, json={"message": "API rate limit exceeded"})

    fail_transport = httpx.MockTransport(fail_handler)
    async with httpx.AsyncClient(transport=fail_transport) as fail_client:
        failing_ingestor = GithubIngestor(client=fail_client, rate_limit_delay=0.0)
        assert await failing_ingestor.check_health() is False


@pytest.mark.asyncio
async def test_github_ingestor_retry_on_rate_limit() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        _ = request
        if attempts == 1:
            return httpx.Response(403, json={"message": "Rate limit exceeded"})
        return httpx.Response(200, json=SAMPLE_GITHUB_SEARCH_RESPONSE)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = GithubIngestor(
            client=client,
            rate_limit_delay=0.0,
            retry_backoff_base=0.01,
        )
        records = [r async for r in ingestor.fetch_records(limit=2)]
        assert len(records) == 2
        assert attempts == 2


@pytest.mark.asyncio
async def test_github_ingestor_rate_limit_exceeded_error_message() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        headers = {"x-ratelimit-remaining": "0"}
        return httpx.Response(403, json={"message": "rate limit exceeded"}, headers=headers)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = GithubIngestor(
            client=client,
            token=None,
            max_retries=1,
            rate_limit_delay=0.0,
            retry_backoff_base=0.01,
        )
        with pytest.raises(RuntimeError, match="GitHub search rate limit exceeded"):
            _ = [r async for r in ingestor.fetch_records(limit=5)]


@pytest.mark.asyncio
async def test_github_ingestor_batch_pagination_stability() -> None:
    requested_params: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_params.append(dict(request.url.params))
        return httpx.Response(200, json=SAMPLE_GITHUB_SEARCH_RESPONSE)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        ingestor = GithubIngestor(
            client=client,
            per_page=30,
            rate_limit_delay=0.0,
        )
        # Limit 20 should request per_page=20, not degrade to per_page=1
        records = [r async for r in ingestor.fetch_records(limit=20)]
        assert len(records) == 2
        assert len(requested_params) == 1
        assert requested_params[0]["per_page"] == "20"
