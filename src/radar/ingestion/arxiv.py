"""arXiv academic pre-print ingestion collector."""

import asyncio
import re
import time
import xml.etree.ElementTree as ET
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import httpx

from radar.core.models import SourcePayload, SourceType
from radar.ingestion.base import BaseIngestor, compute_engagement_velocity

# XML Namespaces for arXiv Atom 1.0 feeds
ATOM_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS = "http://arxiv.org/schemas/atom"
NAMESPACES = {
    "atom": ATOM_NS,
    "arxiv": ARXIV_NS,
}

DEFAULT_USER_AGENT = (
    "TrendHorizonRadar/0.1.0 (+https://github.com/cdr74/trend_research; mailto:radar@example.com)"
)


def _clean_text(text: str | None) -> str:
    """Normalize multi-line XML text, collapsing excess whitespace and newlines."""
    if not text:
        return ""
    return " ".join(text.split())


def _format_authors(authors: list[str]) -> str | None:
    """Format authors list into human-readable citation attribution."""
    if not authors:
        return None
    if len(authors) == 1:
        return authors[0]
    if len(authors) == 2:
        return f"{authors[0]} & {authors[1]}"
    return f"{authors[0]} et al."


def _parse_arxiv_id(raw_id: str) -> tuple[str, str]:
    """Extract bare arXiv ID and version number from a canonical URL or string."""
    clean_id = raw_id.split("/abs/")[-1].strip()
    match = re.search(r"^(.*?)(v\d+)?$", clean_id)
    if match:
        bare_id = match.group(1)
        version = match.group(2) or "v1"
        return bare_id, version
    return clean_id, "v1"


def parse_arxiv_atom_feed(xml_text: str, authority_weight: float = 1.3) -> list[SourcePayload]:
    """Parse an arXiv Atom XML feed into normalized SourcePayload instances."""
    root = ET.fromstring(xml_text)
    entries = root.findall("atom:entry", NAMESPACES)
    records: list[SourcePayload] = []

    for entry in entries:
        # 1. Identifier and URLs
        id_el = entry.find("atom:id", NAMESPACES)
        raw_id_url = id_el.text.strip() if id_el is not None and id_el.text else ""
        bare_id, version = _parse_arxiv_id(raw_id_url)

        pdf_url: str | None = None
        canonical_abs_url: str | None = None
        for link in entry.findall("atom:link", NAMESPACES):
            href = link.attrib.get("href", "")
            title = link.attrib.get("title", "")
            rel = link.attrib.get("rel", "")
            link_type = link.attrib.get("type", "")

            if title == "pdf" or link_type == "application/pdf":
                pdf_url = href
            elif rel == "alternate":
                canonical_abs_url = href

        source_url = canonical_abs_url or raw_id_url

        # 2. Title and Summary (Abstract)
        title_el = entry.find("atom:title", NAMESPACES)
        title = _clean_text(title_el.text) if title_el is not None else ""

        summary_el = entry.find("atom:summary", NAMESPACES)
        raw_content = _clean_text(summary_el.text) if summary_el is not None else ""

        # 3. Authors
        author_names: list[str] = []
        for author_el in entry.findall("atom:author", NAMESPACES):
            name_el = author_el.find("atom:name", NAMESPACES)
            if name_el is not None and name_el.text:
                author_names.append(_clean_text(name_el.text))
        author = _format_authors(author_names)

        # 4. Dates
        published_date: datetime | None = None
        published_el = entry.find("atom:published", NAMESPACES)
        if published_el is not None and published_el.text:
            dt = datetime.fromisoformat(published_el.text.strip().replace("Z", "+00:00"))
            published_date = dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)

        # 5. Categories
        primary_cat_el = entry.find("arxiv:primary_category", NAMESPACES)
        primary_category = primary_cat_el.attrib.get("term") if primary_cat_el is not None else None

        categories: list[str] = []
        for cat_el in entry.findall("atom:category", NAMESPACES):
            term = cat_el.attrib.get("term")
            if term and term not in categories:
                categories.append(term)

        # 6. Additional arXiv metadata
        doi_el = entry.find("arxiv:doi", NAMESPACES)
        doi = doi_el.text.strip() if doi_el is not None and doi_el.text else None

        comment_el = entry.find("arxiv:comment", NAMESPACES)
        comment = _clean_text(comment_el.text) if comment_el is not None else None

        journal_ref_el = entry.find("arxiv:journal_ref", NAMESPACES)
        journal_ref = _clean_text(journal_ref_el.text) if journal_ref_el is not None else None

        metadata: dict[str, Any] = {
            "arxiv_id": bare_id,
            "version": version,
            "primary_category": primary_category,
            "categories": categories,
            "authors": author_names,
            "pdf_url": pdf_url,
            "doi": doi,
            "comment": comment,
            "journal_ref": journal_ref,
        }

        # 7. Initial Telemetry & Velocity
        velocity = compute_engagement_velocity(
            telemetry={"citations": 0.0},
            published_date=published_date,
            source_authority_weight=authority_weight,
        )
        engagement_metrics = {
            "citations": 0.0,
            "velocity": velocity,
        }

        records.append(
            SourcePayload(
                source_type=SourceType.ARXIV,
                source_url=source_url,
                title=title,
                raw_content=raw_content,
                author=author,
                published_date=published_date,
                metadata=metadata,
                engagement_metrics=engagement_metrics,
            )
        )

    return records


class ArxivIngestor(BaseIngestor):
    """Asynchronous pre-print collector querying arXiv's public Atom XML API."""

    name: str = "arxiv"
    source_type: SourceType = SourceType.ARXIV
    source_authority_weight: float = 1.3

    def __init__(
        self,
        endpoint_url: str = "https://export.arxiv.org/api/query",
        search_query: str = "cat:cs.SE",
        authority_weight: float = 1.3,
        sort_by: str = "submittedDate",
        sort_order: str = "descending",
        client: httpx.AsyncClient | None = None,
        rate_limit_delay: float = 3.0,
        user_agent: str = DEFAULT_USER_AGENT,
        max_retries: int = 3,
        retry_backoff_base: float = 2.0,
        page_size: int = 50,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.search_query = search_query
        self.source_authority_weight = authority_weight
        self.sort_by = sort_by
        self.sort_order = sort_order
        self._client = client
        self.rate_limit_delay = rate_limit_delay
        self.user_agent = user_agent
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base
        self.page_size = page_size
        self._last_request_time: float = 0.0

    async def _throttle(self) -> None:
        """Enforce polite delay between sequential API calls."""
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
        """Execute HTTP GET with exponential backoff on HTTP 429/503 errors."""
        headers = {"User-Agent": self.user_agent}

        for attempt in range(self.max_retries + 1):
            await self._throttle()
            resp = await client.get(self.endpoint_url, params=params, headers=headers)
            if resp.status_code in (429, 503) and attempt < self.max_retries:
                wait_time = self.retry_backoff_base * (2**attempt)
                await asyncio.sleep(wait_time)
                continue
            resp.raise_for_status()
            return resp

        # Fallback unreachable due to loop raising, but keeps typechecker satisfied
        raise RuntimeError(f"Failed to query arXiv after {self.max_retries} retries")

    async def fetch_records(
        self,
        since: datetime | None = None,
        limit: int = 50,
    ) -> AsyncGenerator[SourcePayload, None]:
        """Fetch and yield normalized SourcePayload instances from arXiv."""
        start = 0
        total_yielded = 0
        page_size = min(limit, self.page_size)

        # Use passed client or manage a localized AsyncClient session
        owns_client = self._client is None
        client = (
            self._client
            if self._client is not None
            else httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        )

        try:
            while total_yielded < limit:
                current_batch_size = min(page_size, limit - total_yielded)
                params: dict[str, str | int] = {
                    "search_query": self.search_query,
                    "start": start,
                    "max_results": current_batch_size,
                    "sortBy": self.sort_by,
                    "sortOrder": self.sort_order,
                }

                resp = await self._send_request(client, params)
                records = parse_arxiv_atom_feed(
                    resp.text, authority_weight=self.source_authority_weight
                )

                if not records:
                    break

                for record in records:
                    # If results are date-descending and an item is older than 'since', stop pagination
                    if (
                        since is not None
                        and record.published_date is not None
                        and record.published_date < since
                    ):
                        return

                    yield record
                    total_yielded += 1
                    if total_yielded >= limit:
                        return

                start += len(records)
                if len(records) < current_batch_size:
                    break
        finally:
            if owns_client:
                await client.aclose()

    async def check_health(self) -> bool:
        """Verify endpoint connectivity and valid feed response."""
        owns_client = self._client is None
        client = (
            self._client
            if self._client is not None
            else httpx.AsyncClient(timeout=10.0, follow_redirects=True)
        )
        try:
            params: dict[str, str | int] = {
                "search_query": "cat:cs.SE",
                "max_results": 1,
            }
            headers = {"User-Agent": self.user_agent}
            resp = await client.get(self.endpoint_url, params=params, headers=headers)
            if resp.status_code == 200 and "<feed" in resp.text:
                return True
            return False
        except Exception:
            return False
        finally:
            if owns_client:
                await client.aclose()
