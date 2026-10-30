"""GitHub open-source repository and topic ingestion collector."""

import asyncio
import time
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import httpx

from radar.core.config import settings
from radar.core.models import SourcePayload, SourceType
from radar.ingestion.base import (
    BaseIngestor,
    EngagementTelemetry,
    compute_engagement_velocity,
)

DEFAULT_USER_AGENT = "TrendHorizonRadar/0.1.0 (+https://github.com/cdr74/trend_research)"


def _parse_github_datetime(dt_str: str | None) -> datetime | None:
    """Parse GitHub ISO 8601 UTC timestamp."""
    if not dt_str:
        return None
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    except (ValueError, TypeError):
        return None


def parse_github_repo_item(item: dict[str, Any], authority_weight: float = 1.1) -> SourcePayload:
    """Normalize a GitHub repository JSON item into a SourcePayload."""
    full_name = item.get("full_name") or item.get("name") or "unknown/repo"
    repo_name = item.get("name") or full_name.split("/")[-1]
    html_url = item.get("html_url") or f"https://github.com/{full_name}"
    description = item.get("description") or ""

    owner_obj = item.get("owner")
    owner = owner_obj.get("login") if isinstance(owner_obj, dict) else None

    # Dates
    pushed_at = _parse_github_datetime(item.get("pushed_at"))
    created_at = _parse_github_datetime(item.get("created_at"))
    published_date = pushed_at or created_at

    # Telemetry
    stars = int(item.get("stargazers_count") or 0)
    forks = int(item.get("forks_count") or 0)
    open_issues = int(item.get("open_issues_count") or 0)

    telemetry = EngagementTelemetry(
        stars=stars,
        forks=forks,
        discussions=open_issues,
    )
    velocity = compute_engagement_velocity(
        telemetry=telemetry,
        published_date=published_date,
        source_authority_weight=authority_weight,
    )

    engagement_metrics: dict[str, float] = {
        "stars": float(stars),
        "forks": float(forks),
        "discussions": float(open_issues),
        "velocity": velocity,
    }

    topics = item.get("topics") or []
    language = item.get("language")
    license_obj = item.get("license")
    license_name = (
        license_obj.get("spdx_id") or license_obj.get("name")
        if isinstance(license_obj, dict)
        else None
    )

    metadata: dict[str, Any] = {
        "repo_name": repo_name,
        "owner": owner,
        "language": language,
        "topics": topics,
        "license": license_name,
        "default_branch": item.get("default_branch"),
        "archived": bool(item.get("archived", False)),
        "pushed_at": item.get("pushed_at"),
        "created_at": item.get("created_at"),
    }

    raw_content = (
        f"{full_name}: {description}\n"
        f"Language: {language or 'Unknown'}\n"
        f"Topics: {', '.join(topics) if topics else 'None'}"
    )

    return SourcePayload(
        source_type=SourceType.GITHUB,
        source_url=html_url,
        title=full_name,
        raw_content=raw_content,
        author=owner,
        published_date=published_date,
        metadata=metadata,
        engagement_metrics=engagement_metrics,
    )


def parse_github_search_response(
    data: dict[str, Any], authority_weight: float = 1.1
) -> list[SourcePayload]:
    """Parse a GitHub search response into a list of normalized SourcePayloads."""
    items = data.get("items") or []
    return [parse_github_repo_item(item, authority_weight) for item in items]


class GithubIngestor(BaseIngestor):
    """Asynchronous collector querying GitHub's repository search API."""

    name: str = "github"
    source_type: SourceType = SourceType.GITHUB
    source_authority_weight: float = 1.1

    def __init__(
        self,
        endpoint_url: str = "https://api.github.com/search/repositories",
        search_query: str = "topic:test-generation sort:updated",
        authority_weight: float = 1.1,
        token: str | None = None,
        per_page: int = 30,
        rate_limit_delay: float = 1.0,
        user_agent: str = DEFAULT_USER_AGENT,
        max_retries: int = 3,
        retry_backoff_base: float = 2.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.search_query = search_query
        self.source_authority_weight = authority_weight
        self.token = token or settings.github_token
        self.per_page = per_page
        self.rate_limit_delay = rate_limit_delay
        self.user_agent = user_agent
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base
        self._client = client
        self._last_request_time: float = 0.0

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": self.user_agent,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _throttle(self) -> None:
        """Enforce rate limit spacing between queries."""
        if self.rate_limit_delay <= 0.0:
            return
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.monotonic()

    async def _send_request(
        self, client: httpx.AsyncClient, params: dict[str, str | int]
    ) -> httpx.Response:
        """Send HTTP GET request with retries on rate limit (403/429)."""
        headers = self._build_headers()

        for attempt in range(self.max_retries + 1):
            await self._throttle()
            resp = await client.get(self.endpoint_url, params=params, headers=headers)
            if resp.status_code in (403, 429) and attempt < self.max_retries:
                retry_after = resp.headers.get("retry-after")
                if retry_after and retry_after.isdigit():
                    wait_time = float(retry_after)
                else:
                    wait_time = self.retry_backoff_base * (2**attempt)
                await asyncio.sleep(wait_time)
                continue

            if resp.status_code in (403, 429):
                remaining = resp.headers.get("x-ratelimit-remaining")
                if remaining == "0" and not self.token:
                    raise RuntimeError(
                        f"GitHub search rate limit exceeded ({resp.status_code}). "
                        "Unauthenticated requests are limited to 10 queries/min. "
                        "Configure GITHUB_TOKEN in your environment or .env for higher quota."
                    )

            resp.raise_for_status()
            return resp

        raise RuntimeError(f"Failed to query GitHub after {self.max_retries} retries")

    async def fetch_records(
        self,
        since: datetime | None = None,
        limit: int = 50,
    ) -> AsyncGenerator[SourcePayload, None]:
        """Fetch and yield normalized GitHub repository signals with stable batch sizes."""
        page = 1
        total_yielded = 0
        request_per_page = min(max(limit, 10), self.per_page)
        is_sorted_by_date = (
            "sort:updated" in self.search_query or "sort:committer-date" in self.search_query
        )
        max_pages = 5

        owns_client = self._client is None
        client = (
            self._client
            if self._client is not None
            else httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        )

        try:
            while total_yielded < limit and page <= max_pages:
                params: dict[str, str | int] = {
                    "q": self.search_query,
                    "per_page": request_per_page,
                    "page": page,
                }

                resp = await self._send_request(client, params)
                records = parse_github_search_response(
                    resp.json(), authority_weight=self.source_authority_weight
                )

                if not records:
                    break

                for record in records:
                    if (
                        since is not None
                        and record.published_date is not None
                        and record.published_date < since
                    ):
                        if is_sorted_by_date:
                            # Results are chronological; all subsequent items are older than cutoff
                            return
                        continue

                    yield record
                    total_yielded += 1
                    if total_yielded >= limit:
                        return

                page += 1
                if len(records) < request_per_page:
                    break
        finally:
            if owns_client:
                await client.aclose()

    async def check_health(self) -> bool:
        """Verify endpoint connectivity and rate-limit headroom."""
        owns_client = self._client is None
        client = (
            self._client
            if self._client is not None
            else httpx.AsyncClient(timeout=10.0, follow_redirects=True)
        )
        try:
            params: dict[str, str | int] = {
                "q": "topic:test-generation",
                "per_page": 1,
            }
            resp = await client.get(
                self.endpoint_url,
                params=params,
                headers=self._build_headers(),
            )
            return resp.status_code == 200
        except Exception:
            return False
        finally:
            if owns_client:
                await client.aclose()
