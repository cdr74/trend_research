"""Practitioner publication RSS 2.0 and Atom 1.0 feed ingestion collector."""

import asyncio
import html
import re
import time
import xml.etree.ElementTree as ET
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import httpx

from radar.core.models import SourcePayload, SourceType
from radar.ingestion.base import (
    BaseIngestor,
    EngagementTelemetry,
    compute_engagement_velocity,
)

DEFAULT_USER_AGENT = (
    "TrendHorizonRadar/0.1.0 (+https://github.com/cdr74/trend_research; mailto:radar@example.com)"
)

# Common XML syndication namespaces
DC_NS = "http://purl.org/dc/elements/1.1/"
CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"
ATOM_NS = "http://www.w3.org/2005/Atom"
NAMESPACES = {
    "dc": DC_NS,
    "content": CONTENT_NS,
    "atom": ATOM_NS,
}


def _clean_html_text(text: str | None) -> str:
    """Strip XML/HTML markup, unescape HTML entities, and collapse whitespace."""
    if not text:
        return ""
    # Strip HTML tags
    no_html = re.sub(r"<[^>]+>", " ", text)
    # Unescape entities (e.g. &amp;, &lt;, &gt;)
    unescaped = html.unescape(no_html)
    return " ".join(unescaped.split())


def _parse_feed_date(date_str: str | None) -> datetime | None:
    """Parse either RFC 822/2822 or ISO 8601 feed timestamps into UTC."""
    if not date_str:
        return None
    cleaned = date_str.strip()

    # Try RFC 2822 (common in RSS 2.0)
    try:
        dt = parsedate_to_datetime(cleaned)
        return dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    except (ValueError, TypeError):
        pass

    # Try ISO 8601 (common in Atom)
    try:
        dt = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        return dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    except (ValueError, TypeError):
        pass

    return None


# Generic testing/eval terms that require co-occurring software qualifiers
_GENERIC_TERMS = {
    "testing",
    "test",
    "tests",
    "verification",
    "verified",
    "verify",
    "benchmarking",
    "benchmark",
    "benchmarks",
    "evals",
    "evaluation",
    "evaluations",
    "automation",
    "automated",
    "qa",
    "quality",
    "ai",
}

# Software engineering qualifiers required when generic terms match
_SE_QUALIFIERS = re.compile(
    r"\b(code|software|ci/cd|pipeline|runner|unit|integration|e2e|assertion|"
    r"regression|harness|test\s+suite|developer|runtime|compiler|mutation|"
    r"flaky|invariant|mock|stub|ast|symbolic|fuzz|bug|defect|commit|repo)\b",
    re.IGNORECASE,
)

# High-confidence standalone terms that qualify immediately (Dual Track)
_STANDALONE_QE_TERMS = re.compile(
    r"\b("
    # Track 1: Software Testing (Deterministic)
    r"mutation\s+testing|property-based\s+testing|differential\s+fuzzing|"
    r"flaky\s+test|predictive\s+test\s+selection|automated\s+program\s+repair|"
    r"test\s+synthesis|concolic\s+execution|canary\s+analysis|chaos\s+engineering|"
    r"test\s+runner|test\s+impact\s+analysis|coverage\s+analysis|fault\s+injection|"
    # Track 2: AI Evaluation (Non-Deterministic)
    r"llm\s+evals|llm-as-a-judge|prompt\s+regression|hallucination\s+detection|"
    r"agent\s+benchmarking|behavioral\s+drift|prompt\s+injection|jailbreak\s+defense|"
    r"adversarial\s+red-teaming|red\s+teaming|"
    # Evidence of Adequacy & Governance
    r"mutation\s+score|evidence\s+of\s+adequacy|proof\s+of\s+testing|confidence\s+score"
    r")\b",
    re.IGNORECASE,
)

# Negative exclusion patterns that disqualify non-technical articles
_NEGATIVE_EXCLUSIONS = re.compile(
    r"\b(marketplace\s+growth|pricing\s+plans?|webinar|hiring\s+now|salary\s+survey|"
    r"promo\s+code|sponsored\s+post|discount\s+code|investor\s+relations)\b",
    re.IGNORECASE,
)


class RelevanceFilter:
    """Tier 1 token-boundary and compound domain relevance filter (Ref: ADR-0021)."""

    @classmethod
    def matches(cls, text: str, keywords: list[str] | None = None) -> bool:
        """Evaluate text using token boundaries, compound co-occurrence, and exclusions."""
        if not text:
            return False

        # Disqualify commercial marketing/job listings
        if _NEGATIVE_EXCLUSIONS.search(text):
            return False

        # If explicit keywords provided, enforce word boundaries and disambiguation
        if keywords:
            for k in keywords:
                cleaned_k = k.strip()
                if not cleaned_k:
                    continue
                # Token-boundary regex to prevent 'ai' in 'email' or 'test' in 'fastest'
                pattern = re.compile(rf"\b{re.escape(cleaned_k)}\b", re.IGNORECASE)
                if pattern.search(text):
                    lowered_k = cleaned_k.lower()
                    if lowered_k in _GENERIC_TERMS:
                        # Require co-occurrence with software engineering context
                        if _SE_QUALIFIERS.search(text) or _STANDALONE_QE_TERMS.search(text):
                            return True
                    else:
                        # Non-generic specific keyword (e.g. 'canary', 'flaky', 'mutation')
                        return True
            return False

        # If no explicit keywords configured, default to standalone QE or generic+qualifier
        if _STANDALONE_QE_TERMS.search(text):
            return True
        if re.search(r"\b(testing|verification|evals|qa)\b", text, re.I) and _SE_QUALIFIERS.search(
            text
        ):
            return True

        return True


def _matches_keywords(text: str, keywords: list[str] | None) -> bool:
    """Evaluate text against keywords using the Tier 1 RelevanceFilter."""
    return RelevanceFilter.matches(text, keywords)


def _parse_rss2_item(
    item_el: ET.Element, authority_weight: float = 1.25, keywords: list[str] | None = None
) -> SourcePayload | None:
    """Parse an individual RSS 2.0 <item> element."""
    title_el = item_el.find("title")
    title = _clean_html_text(title_el.text) if title_el is not None else ""

    link_el = item_el.find("link")
    link = link_el.text.strip() if link_el is not None and link_el.text else ""

    # Prefer <content:encoded>, fallback to <description>
    content_el = item_el.find("content:encoded", NAMESPACES)
    desc_el = item_el.find("description")
    raw_content = ""
    if content_el is not None and content_el.text:
        raw_content = _clean_html_text(content_el.text)
    elif desc_el is not None and desc_el.text:
        raw_content = _clean_html_text(desc_el.text)

    # Keyword relevance filter
    combined_text = f"{title} {raw_content}"
    if not _matches_keywords(combined_text, keywords):
        return None

    # Author (<dc:creator> or <author>)
    creator_el = item_el.find("dc:creator", NAMESPACES)
    author_el = item_el.find("author")
    author: str | None = None
    if creator_el is not None and creator_el.text:
        author = _clean_html_text(creator_el.text)
    elif author_el is not None and author_el.text:
        author = _clean_html_text(author_el.text)

    # Date (<pubDate> or <dc:date>)
    pub_date_el = item_el.find("pubDate")
    dc_date_el = item_el.find("dc:date", NAMESPACES)
    raw_date = pub_date_el.text if pub_date_el is not None else None
    if not raw_date and dc_date_el is not None:
        raw_date = dc_date_el.text
    published_date = _parse_feed_date(raw_date)

    # Categories
    categories = [
        _clean_html_text(c.text) for c in item_el.findall("category") if c.text and c.text.strip()
    ]

    # Telemetry baseline for engineering blogs (100 estimated reader views)
    telemetry = EngagementTelemetry(views=100)
    velocity = compute_engagement_velocity(
        telemetry=telemetry,
        published_date=published_date,
        source_authority_weight=authority_weight,
    )

    return SourcePayload(
        source_type=SourceType.RSS,
        source_url=link,
        title=title,
        raw_content=raw_content,
        author=author,
        published_date=published_date,
        metadata={"categories": categories, "feed_format": "rss2"},
        engagement_metrics={"views": 100.0, "velocity": velocity},
    )


def _find_elem(parent: ET.Element, tag: str, ns_prefix: str = "atom") -> ET.Element | None:
    """Find a child element checking namespace first, then direct tag."""
    el = parent.find(f"{ns_prefix}:{tag}", NAMESPACES)
    if el is not None:
        return el
    el = parent.find(f"{{{ATOM_NS}}}{tag}")
    if el is not None:
        return el
    return parent.find(tag)


def _findall_elems(parent: ET.Element, tag: str, ns_prefix: str = "atom") -> list[ET.Element]:
    """Find all child elements checking namespace first, then direct tag."""
    elems = parent.findall(f"{ns_prefix}:{tag}", NAMESPACES)
    if elems:
        return elems
    elems = parent.findall(f"{{{ATOM_NS}}}{tag}")
    if elems:
        return elems
    return parent.findall(tag)


def _parse_atom_entry(
    entry_el: ET.Element, authority_weight: float = 1.25, keywords: list[str] | None = None
) -> SourcePayload | None:
    """Parse an individual Atom 1.0 <entry> element."""
    title_el = _find_elem(entry_el, "title")
    title = _clean_html_text(title_el.text) if title_el is not None else ""

    # Link: prefer rel="alternate", fallback to href
    link = ""
    for link_el in _findall_elems(entry_el, "link"):
        href = link_el.attrib.get("href", "")
        rel = link_el.attrib.get("rel", "alternate")
        if rel == "alternate" and href:
            link = href
            break
        if href and not link:
            link = href

    # Content / Summary
    content_el = _find_elem(entry_el, "content")
    summary_el = _find_elem(entry_el, "summary")
    raw_content = ""
    if content_el is not None and content_el.text:
        raw_content = _clean_html_text(content_el.text)
    elif summary_el is not None and summary_el.text:
        raw_content = _clean_html_text(summary_el.text)

    # Keyword check
    if not _matches_keywords(f"{title} {raw_content}", keywords):
        return None

    # Author
    author_el = _find_elem(entry_el, "author")
    author: str | None = None
    if author_el is not None:
        name_el = _find_elem(author_el, "name")
        if name_el is not None and name_el.text:
            author = _clean_html_text(name_el.text)

    # Date: published or updated
    pub_el = _find_elem(entry_el, "published")
    upd_el = _find_elem(entry_el, "updated")
    raw_date = pub_el.text if pub_el is not None else (upd_el.text if upd_el is not None else None)
    published_date = _parse_feed_date(raw_date)

    # Categories
    categories: list[str] = []
    for cat_el in _findall_elems(entry_el, "category"):
        term = cat_el.attrib.get("term")
        if term:
            categories.append(term)

    telemetry = EngagementTelemetry(views=100)
    velocity = compute_engagement_velocity(
        telemetry=telemetry,
        published_date=published_date,
        source_authority_weight=authority_weight,
    )

    return SourcePayload(
        source_type=SourceType.RSS,
        source_url=link,
        title=title,
        raw_content=raw_content,
        author=author,
        published_date=published_date,
        metadata={"categories": categories, "feed_format": "atom"},
        engagement_metrics={"views": 100.0, "velocity": velocity},
    )


def parse_syndication_feed(
    xml_text: str, authority_weight: float = 1.25, keywords: list[str] | None = None
) -> list[SourcePayload]:
    """Parse RSS 2.0 or Atom 1.0 XML into normalized SourcePayloads."""
    root = ET.fromstring(xml_text)
    records: list[SourcePayload] = []

    # Detect root tag type
    root_tag = root.tag.lower()
    if root_tag.endswith("rss"):
        channel = root.find("channel")
        if channel is not None:
            for item in channel.findall("item"):
                payload = _parse_rss2_item(
                    item, authority_weight=authority_weight, keywords=keywords
                )
                if payload is not None:
                    records.append(payload)
    elif root_tag.endswith("feed"):
        entries = _findall_elems(root, "entry")
        for entry in entries:
            payload = _parse_atom_entry(entry, authority_weight=authority_weight, keywords=keywords)
            if payload is not None:
                records.append(payload)

    return records


class RssFeedIngestor(BaseIngestor):
    """Asynchronous collector querying RSS 2.0 and Atom feeds of tech publications."""

    name: str = "rss"
    source_type: SourceType = SourceType.RSS
    source_authority_weight: float = 1.25

    def __init__(
        self,
        endpoint_url: str = "https://netflixtechblog.com/feed",
        authority_weight: float = 1.25,
        keywords: list[str] | None = None,
        rate_limit_delay: float = 1.0,
        user_agent: str = DEFAULT_USER_AGENT,
        max_retries: int = 3,
        retry_backoff_base: float = 2.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.endpoint_url = endpoint_url
        self.source_authority_weight = authority_weight
        self.keywords = keywords
        self.rate_limit_delay = rate_limit_delay
        self.user_agent = user_agent
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base
        self._client = client
        self._last_request_time: float = 0.0

    async def _throttle(self) -> None:
        """Pace requests to remote publication endpoints."""
        if self.rate_limit_delay <= 0.0:
            return
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.monotonic()

    async def fetch_records(
        self,
        since: datetime | None = None,
        limit: int = 50,
    ) -> AsyncGenerator[SourcePayload, None]:
        """Fetch and yield normalized article records from the RSS/Atom feed."""
        owns_client = self._client is None
        client = (
            self._client
            if self._client is not None
            else httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        )

        headers = {"User-Agent": self.user_agent}

        try:
            await self._throttle()
            resp = await client.get(self.endpoint_url, headers=headers)
            resp.raise_for_status()

            records = parse_syndication_feed(
                resp.text,
                authority_weight=self.source_authority_weight,
                keywords=self.keywords,
            )

            total_yielded = 0
            for record in records:
                if (
                    since is not None
                    and record.published_date is not None
                    and record.published_date < since
                ):
                    continue

                yield record
                total_yielded += 1
                if total_yielded >= limit:
                    break
        finally:
            if owns_client:
                await client.aclose()

    async def check_health(self) -> bool:
        """Verify feed connectivity and XML integrity."""
        owns_client = self._client is None
        client = (
            self._client
            if self._client is not None
            else httpx.AsyncClient(timeout=10.0, follow_redirects=True)
        )
        try:
            resp = await client.get(self.endpoint_url, headers={"User-Agent": self.user_agent})
            if resp.status_code == 200 and ("<rss" in resp.text or "<feed" in resp.text):
                return True
            return False
        except Exception:
            return False
        finally:
            if owns_client:
                await client.aclose()
