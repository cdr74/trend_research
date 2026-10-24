# ADR 0006: Academic Pre-Print Ingestion Collector (arXiv Atom API)

## Status
Accepted

## Context
Milestone 2 (Backlog item `M2-T2`) requires ingesting academic pre-prints to seed the radar with emerging technical breakthroughs prior to commercialization or open-source repackaging. The Software Quality Engineering domain profile specifically monitors `cs.SE` (Software Engineering), `cs.AI` (Artificial Intelligence), and `cs.PL` (Programming Languages).

Academic venue data provides the highest source authority weight ($W_{\text{auth}} = 1.3$) in the Radar scoring matrix. Ingested records must be normalized into `SourcePayload` instances adhering to the `BaseIngestor` protocol defined in `src/radar/ingestion/base.py`.

The collector must operate reliably under the following operational requirements:
1. **Public Zero-Auth Operation:** Ingestion must function out-of-the-box in local and CI environments without mandatory proprietary API keys or paid subscriptions.
2. **Polite API Etiquette:** arXiv's Terms of Service and API Guidelines mandate:
   - Identifying the client via a descriptive `User-Agent` containing contact/repository information.
   - Pacing queries with at least a 3.0-second delay between requests to protect export server stability.
   - Graceful handling of HTTP 429 (Too Many Requests) and HTTP 503 (Service Unavailable) using exponential backoff.
3. **Structured Atom 1.0 XML Parsing:** Pre-print records must be parsed into timezone-aware UTC dates, cleaned titles/summaries (stripping whitespace and LaTeX-like artifacts), structured author lists, primary and secondary categories, DOI references, and canonical PDF/abstract URLs.
4. **Offline Test Parity:** Tests must run deterministically without internet dependencies by mocking HTTP transport layers with synthetic or recorded Atom XML fixtures.

## Options Considered

### Option 1: Native Standard Library `xml.etree.ElementTree` with `httpx.AsyncClient` (Selected)
- Use Python's built-in `xml.etree.ElementTree` with explicit Atom XML namespace mappings (`{http://www.w3.org/2005/Atom}`, `{http://arxiv.org/schemas/atom}`).
- Use `httpx.AsyncClient` (already a project dependency) for asynchronous HTTP requests with rate limiting and exponential retry backoff.
- *Pros:* Zero additional third-party dependencies; fully asynchronous; strictly typed (`mypy --strict` compliant); easily testable via `httpx.MockTransport`.
- *Cons:* Requires explicit handling of XML namespaces and text normalization.

### Option 2: Third-Party `arxiv` Python Package (`arxiv.py`)
- Python wrapper maintained by the community around arXiv's API.
- *Pros:* High-level convenience methods.
- *Cons:* Synchronous blocking I/O using standard `urllib`; incompatible with `asyncio` DAG pipeline without thread pool offloading; introduces external dependency with opinionated pagination models.

### Option 3: Third-Party `feedparser` / `defusedxml`
- Feedparser library for RSS/Atom syndication parsing.
- *Pros:* Flexible parsing across ill-formed RSS feeds.
- *Cons:* Unmaintained/loose typing causing `mypy --strict` friction; synchronous I/O; adds runtime bloat for arXiv's well-structured, standardized Atom feed.

## Decision Rationale
We select **Option 1**: A dedicated asynchronous `ArxivIngestor` client built with `httpx.AsyncClient` and Python standard library `xml.etree.ElementTree`.

Key Architectural Decisions:
1. **Protocol Compliance:** `ArxivIngestor` implements `BaseIngestor`, exposing:
   - `fetch_records(since: datetime | None, limit: int) -> AsyncGenerator[SourcePayload, None]`
   - `check_health() -> bool`
2. **Polite Throttling & Backoff:** Configurable rate-limiting delay (defaulting to 3.0s per arXiv guidelines) that can be set to 0.0s during test execution. Implements retry with exponential backoff on transient HTTP 429/503 errors.
3. **Robust Atom XML Parsing:**
   - Namespaces: `ATOM = "http://www.w3.org/2005/Atom"`, `ARXIV = "http://arxiv.org/schemas/atom"`.
   - Title and summary newlines/multi-spaces normalized into single spaced clean text.
   - Dates parsed via `datetime.fromisoformat` and converted to UTC.
   - Canonical URLs (`http://arxiv.org/abs/...`), arXiv ID extraction, authors, and category tags stored in structured metadata.
4. **Hermetic Testing:** Mock transport fixtures in `tests/unit/test_arxiv_ingestor.py` verifying full end-to-end payload extraction, date filtering (`since`), and health checks without outbound network traffic.

## Consequences

### Positive
- Fully native async pipeline integration without blocking the event loop.
- Zero added dependencies to `pyproject.toml`.
- Strict typing and linting adherence with 100% test coverage.
- Fully respectful of arXiv API service guidelines.

### Negative / Trade-offs
- If arXiv introduces breaking schema changes to its Atom feed, parsing logic in `ArxivIngestor` must be manually updated and validated against new fixtures.
