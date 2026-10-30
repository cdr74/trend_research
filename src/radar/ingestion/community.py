"""Community discussion and telemetry ingestion collector (HackerNews / Algolia Search)."""

import asyncio
import time
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import httpx

from radar.core.models import SourcePayload, SourceType
from radar.ingestion.base import (
    BaseIngestor,
    EngagementTelemetry,
    compute_engagement_velocity,
)

DEFAULT_USER_AGENT = "TrendHorizonRadar/0.1.0 (+https://github.com/cdr74/trend_research)"


def _parse_hn_datetime(dt_str: str | None) -> datetime | None:
    """Parse ISO 8601 UTC timestamp from HackerNews API."""
    if not dt_str:
        return None
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    except (ValueError, TypeError):
        return None


def parse_hn_story_item(
    item: dict[str, Any], authority_weight: float = 0.85
) -> SourcePayload | None:
    """Normalize a HackerNews Algolia search story item into a SourcePayload."""
    object_id = str(item.get("objectID") or "").strip()
    title = str(item.get("title") or "").strip()
    if not title:
        return None

    # Canonical URL: prefer story URL, fallback to internal HN discussion
    hn_item_url = (
        f"https://news.ycombinator.com/item?id={object_id}"
        if object_id
        else "https://news.ycombinator.com"
    )
    source_url = str(item.get("url") or hn_item_url).strip()

    # Content: story text or title
    story_text = item.get("story_text") or ""
    raw_content = str(story_text).strip() if story_text else title

    author = item.get("author")
    published_date = _parse_hn_datetime(item.get("created_at"))

    points = int(item.get("points") or 0)
    comments = int(item.get("num_comments") or 0)

    # Community telemetry: points map to estimated views; comments map to discussions
    telemetry = EngagementTelemetry(
        views=points * 10,
        discussions=comments,
    )
    velocity = compute_engagement_velocity(
        telemetry=telemetry,
        published_date=published_date,
        source_authority_weight=authority_weight,
    )

    engagement_metrics: dict[str, float] = {
        "points": float(points),
        "comments": float(comments),
        "velocity": velocity,
    }

    metadata: dict[str, Any] = {
        "object_id": object_id,
        "hn_item_url": hn_item_url,
        "points": points,
        "comments": comments,
        "created_at_i": item.get("created_at_i"),
    }

    return SourcePayload(
        source_type=SourceType.COMMUNITY,
        source_url=source_url,
        title=title,
        raw_content=raw_content,
        author=author,
        published_date=published_date,
        metadata=metadata,
        engagement_metrics=engagement_metrics,
    )


class HnAlgoliaIngestor(BaseIngestor):
    """Asynchronous collector querying HackerNews stories via Algolia Search API."""

    name: str = "community"
    source_type: SourceType = SourceType.COMMUNITY
    source_authority_weight: float = 0.85

    def __init__(
        self,
        endpoint_url: str = "https://hn.algolia.com/api/v1/search_by_date",
        search_query: str = "mutation testing OR test generation OR flaky tests OR LLM evals",
        tags: str = "story",
        authority_weight: float = 0.85,
        rate_limit_delay: float = 0.2,
        user_agent: str = DEFAULT_USER_AGENT,
        max_retries: int = 3,
        retry_backoff_base: float = 1.5,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.search_query = search_query
        self.tags = tags
        self.source_authority_weight = authority_weight
        self.rate_limit_delay = rate_limit_delay
        self.user_agent = user_agent
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base
        self._client = client
        self._last_request_time: float = 0.0

    async def _throttle(self) -> None:
        """Pace requests to Algolia search API."""
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
        """Send HTTP GET request with retries."""
        headers = {
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }

        for attempt in range(self.max_retries + 1):
            await self._throttle()
            resp = await client.get(self.endpoint_url, params=params, headers=headers)
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                wait_time = self.retry_backoff_base * (2**attempt)
                await asyncio.sleep(wait_time)
                continue
            resp.raise_for_status()
            return resp

        raise RuntimeError(
            f"Failed to query HackerNews Algolia API after {self.max_retries} retries"
        )

    async def fetch_records(
        self,
        since: datetime | None = None,
        limit: int = 50,
    ) -> AsyncGenerator[SourcePayload, None]:
        """Fetch and yield normalized HackerNews stories."""
        # Deconstruct disjunctive queries into individual search terms
        terms = [t.strip() for t in self.search_query.split(" OR ") if t.strip()]
        if not terms:
            terms = [self.search_query]

        owns_client = self._client is None
        client = (
            self._client
            if self._client is not None
            else httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        )

        seen_urls: set[str] = set()
        total_yielded = 0

        try:
            for term in terms:
                if total_yielded >= limit:
                    break

                hits_needed = limit - total_yielded
                params: dict[str, str | int] = {
                    "query": term,
                    "tags": self.tags,
                    "hitsPerPage": min(hits_needed, 50),
                }
                if since is not None:
                    since_ts = int(since.timestamp())
                    params["numericFilters"] = f"created_at_i>={since_ts}"

                resp = await self._send_request(client, params)
                data = resp.json()
                hits = data.get("hits", [])

                for item in hits:
                    payload = parse_hn_story_item(
                        item, authority_weight=self.source_authority_weight
                    )
                    if payload is None:
                        continue
                    if payload.source_url in seen_urls:
                        continue

                    if (
                        since is not None
                        and payload.published_date is not None
                        and payload.published_date < since
                    ):
                        continue

                    seen_urls.add(payload.source_url)
                    yield payload
                    total_yielded += 1
                    if total_yielded >= limit:
                        return
        finally:
            if owns_client:
                await client.aclose()

    async def check_health(self) -> bool:
        """Verify endpoint connectivity."""
        owns_client = self._client is None
        client = (
            self._client
            if self._client is not None
            else httpx.AsyncClient(timeout=10.0, follow_redirects=True)
        )
        try:
            resp = await client.get(
                self.endpoint_url,
                params={"hitsPerPage": 1},
                headers={"User-Agent": self.user_agent},
            )
            return resp.status_code == 200
        except Exception:
            return False
        finally:
            if owns_client:
                await client.aclose()
