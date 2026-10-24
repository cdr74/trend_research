# ADR 0008: Practitioner Publication & Media Ingestion Collector (RSS / Atom)

## Status
Accepted

## Context
Milestone 2 (Backlog item `M2-T4`) requires ingesting practitioner engineering blogs, post-mortems, and case studies (e.g., Netflix Tech Blog, Uber Engineering, Meta Engineering, Martin Fowler Bliki). In the Software Quality Engineering domain profile, engineering blogs provide crucial real-world failure modes, chaos engineering outcomes, and deployment reliability findings ($W_{\text{auth}} = 1.25$).

Engineering blogs predominantly syndicate content via standard RSS 2.0 or Atom 1.0 XML feeds. The collector must parse feeds from diverse enterprise content management systems (Medium, WordPress, custom static sites) reliably and normalize them into `SourcePayload` models.

## Requirements & Constraints
1. **Dual RSS 2.0 & Atom 1.0 Support:**
   - Seamlessly parse `<rss><channel><item>` (RSS 2.0) and `<feed><entry>` (Atom 1.0) feeds through a single unified parser.
2. **Robust Date Parsing:**
   - RSS 2.0 feeds format dates via RFC 822 / RFC 2822 (e.g., `Wed, 23 Oct 2024 14:00:00 GMT`).
   - Atom feeds format dates via ISO 8601 (e.g., `2024-10-23T14:00:00Z`).
   - Dates must normalize to UTC timezone-aware datetimes.
3. **HTML Sanitization & Summary Normalization:**
   - Feed content frequently embeds raw HTML tags (`<p>`, `<a>`, `<pre>`), CDATA blocks, and encoded entities.
   - Summaries must be stripped of HTML markup and normalized into readable plain text for downstream NLP processing and noise sifting.
4. **Keyword & Topic Filtering:**
   - Feeds often publish general technology articles. The collector must support optional keyword filtering (e.g., `testing`, `chaos`, `canary`, `reliability`, `verification`) to focus on relevant domain signals.
5. **Offline Test Parity:**
   - Comprehensive unit test coverage for RSS 2.0 and Atom feeds, date format variations, malformed feeds, and HTML stripping without hitting external servers.

## Options Considered

### Option 1: Native Standard Library `xml.etree.ElementTree` + `email.utils` (Selected)
- Use standard library `xml.etree.ElementTree` for XML parsing.
- Use `email.utils.parsedate_to_datetime` for RFC 822/2822 dates, and `datetime.fromisoformat` for ISO 8601 dates.
- Use regex/`html` parser to strip HTML tags from summaries.
- *Pros:* Zero additional external dependencies; async-friendly; fully type-safe (`mypy --strict`); predictable error handling.
- *Cons:* Requires custom logic to branch between RSS 2.0 and Atom root structures.

### Option 2: Third-Party `feedparser`
- Legacy syndication feed parser in Python.
- *Pros:* Handles very broken HTML/XML feeds.
- *Cons:* Synchronous blocking I/O; poor type annotations requiring `# type: ignore` across code; heavy baggage for standard modern tech blogs.

## Decision Rationale
We select **Option 1**: A lightweight, async `RssFeedIngestor` built with `httpx.AsyncClient` and standard library `xml.etree.ElementTree`.

Key Design Specifications:
1. **Unified Root Detection:**
   - Inspects the XML root tag: if `feed` or contains `Atom`, parses as Atom entries; if `rss`, parses `channel/item` elements.
2. **Date Extraction Strategy:**
   - Checks `pubDate`, `dc:date`, `published`, `updated`.
   - Parses RFC 2822 dates using `email.utils.parsedate_to_datetime`, falling back to `datetime.fromisoformat`.
3. **Text Cleaning:**
   - Strips XML/HTML tags with regex `re.sub(r"<[^>]+>", " ", text)` and normalizes whitespace with `_clean_text`.
4. **Authority & Telemetry:**
   - Applies $W_{\text{auth}} = 1.25$.
   - Computes initial velocity using published date.

## Consequences

### Positive
- Unified connector capable of ingesting any standard RSS 2.0 or Atom 1.0 engineering publication.
- Zero added dependencies to `pyproject.toml`.
- Strict typing compliance and full testability via mock HTTP transports.

### Negative / Trade-offs
- Feeds with non-standard proprietary date formats or malformed non-XML markup will require fallback error handling.
