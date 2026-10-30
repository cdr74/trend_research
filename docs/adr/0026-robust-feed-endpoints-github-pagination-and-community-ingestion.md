# ADR 0026: Robust Feed Endpoints, GitHub Pagination & Community Ingestion

## Status
Accepted (Phase 2 Autonomous Implementation)

## Context
During live incremental synchronization (`uv run radar sync --days 365`), several source stream errors and ingestion volume discrepancies were identified:
1. **Source Stream Failures:**
   - `uber-eng-blog`: The endpoint `https://www.uber.com/US/en/blog/engineering/rss/` returned HTTP 406 / 404 because Uber decommissioned their public RSS feed.
   - `software-testing-weekly`: The URL `https://softwaretestingweekly.com/feed/` returned HTTP 404 because Ghost issue syndication is published at `https://softwaretestingweekly.com/issues/rss/`.
   - `hackernews-test-topics`: The Algolia search endpoint returns JSON (`{"hits": [...]}`), but `src/radar/presentation/cli.py` routed all `community` channels to `RssFeedIngestor`, causing XML parser failures (`not well-formed (invalid token): line 1, column 0`).
   - `github-topic-property-based-testing`: Hit HTTP 403 rate limits on GitHub Search API.
2. **GitHub Search Ingestion Rate-Limit Depletion:**
   - `GithubIngestor.fetch_records` dynamically computed `current_per_page = min(batch_size, limit - total_yielded)`. When approaching the limit (e.g. 19/20 items yielded), `current_per_page` reduced to `1`, triggering repeated single-item page requests (`page=2`, `page=3`, etc.) that rapidly consumed the unauthenticated GitHub rate quota of 10 requests per minute.
3. **Syndication Depth and CLI Limit Semantics:**
   - Standard engineering feeds (Netflix, Meta) only publish their latest 9–10 posts in XML.
   - High-volume sources (arXiv, GitHub search) are capped by the CLI default `--limit-per-source 20`.

---

## Decision Matrix & Architecture

### 1. Catalog Endpoint Remediation (`data/seeds/sources.yaml`)
* **Software Testing Weekly:** Correct endpoint to `https://softwaretestingweekly.com/issues/rss/`.
* **Uber Engineering Blog Decommissioning & Replacement:**
  - Mark `uber-eng-blog` as `enabled: false` with documentation noting the official feed removal.
  - Introduce `cloudflare-eng-blog` (`https://blog.cloudflare.com/rss/`) targeting distributed systems reliability, sandbox testing, and edge fuzzing.

### 2. GitHub Ingestor Batch Stabilization & Safety Boundary
* **Decision:**
  - Maintain stable batch sizes (`per_page = min(max(limit, 10), self.per_page)`) rather than decrementing down to 1 item per page.
  - Introduce an upper bound ceiling (`max_pages = 5`) per search stream to prevent runaway pagination when candidate repositories are filtered out by timestamp.
  - Gracefully log rate-limit reset times upon receiving 403 or 429 status codes.

### 3. Dedicated HackerNews / Algolia Community Ingestor
* **Decision:**
  - Add `SourceType.COMMUNITY = "community"` to `radar.core.models.SourceType`.
  - Implement `HnAlgoliaIngestor` in `src/radar/ingestion/community.py` inheriting from `BaseIngestor`.
  - Support disjunctive search queries (`"term1 OR term2"`) by querying Algolia for each term and deduplicating by story URL/ID.
  - Leverage Algolia's native timestamp filtering (`numericFilters="created_at_i>=<since_ts>"`) and capture story `points` and `num_comments` into engagement telemetry.
  - Update `cli.py` to route `src.channel == "community"` to `HnAlgoliaIngestor` and pass configured `keywords` to `RssFeedIngestor`.

---

## Consequences

### Positive
- All 15 source streams synchronize cleanly without uncaught HTTP 404, 406, or XML parsing exceptions.
- GitHub search queries consume a fraction of API requests, preventing 403 rate-limiting in unauthenticated environments.
- HackerNews community pulse and sentiment are ingested as first-class signals with upvote and discussion telemetry.

### Negative / Trade-offs
- The unauthenticated GitHub Search API remains bounded to 10 req/min; users with large numbers of enabled GitHub topics should set `GITHUB_TOKEN` for extended quota headroom.
