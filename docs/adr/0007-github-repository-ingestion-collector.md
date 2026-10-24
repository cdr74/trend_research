# ADR 0007: Open Source Repository & Metrics Collector (GitHub Ingestor)

## Status
Accepted

## Context
Milestone 2 (Backlog item `M2-T3`) requires tracking open-source repository velocity, developer traction, and code release cadence. In the Software Quality Engineering domain profile, open-source projects provide early indicators of developer adoption for test generation frameworks, mutation testing engines, AI eval tools, and browser automation agents.

Unlike static document feeds, open-source repositories provide live, high-frequency engagement telemetry:
- Stargazers count ($S$)
- Forks count ($F$)
- Open issues / PR discussion activity ($D$)
- Recency of commits/pushes ($\Delta t$)

This telemetry directly feeds into the engagement velocity formula established in ADR-0000 and implemented in `src/radar/ingestion/base.py`:
$$\text{Velocity} = \frac{\Delta \text{Engagement}}{\Delta t} \times W_{\text{auth}}$$
With $W_{\text{auth}} = 1.1$ for open-source repositories.

## Requirements & Constraints
1. **Zero-Token Public Fallback:** The connector must function without mandatory API credentials, utilizing GitHub's public REST API search endpoint (`https://api.github.com/search/repositories`) up to the unauthenticated rate limit (60 requests/hour).
2. **Authenticated Escalation:** If a `GITHUB_TOKEN` is configured via environment or settings, the connector must attach the Bearer token to increase rate limit capacity to 5,000 requests/hour.
3. **Robust Rate-Limit & Backoff Handling:** The client must inspect `x-ratelimit-remaining` and `x-ratelimit-reset` headers, pausing or backing off on HTTP 403/429 rather than terminating runs.
4. **Normalized Schema Mapping:** Each repository item must normalize into a `SourcePayload` with `SourceType.GITHUB`, storing structured metadata (`repo_name`, `owner`, `topics`, `language`, `license`, `pushed_at`, `created_at`).
5. **Offline Test Parity:** All tests must run hermetically without outbound network traffic using mocked JSON payloads via `httpx.MockTransport`.

## Options Considered

### Option 1: Native `httpx.AsyncClient` with GitHub REST API v3 (Selected)
- Use `httpx.AsyncClient` to query `https://api.github.com/search/repositories`.
- Parse JSON search results into `SourcePayload`.
- *Pros:* Fully asynchronous; zero additional third-party dependencies; strictly typed; easily mocked; uniform error handling across all collectors.
- *Cons:* Subject to GitHub search API limits (1,000 results per query, max 100 per page).

### Option 2: GitHub GraphQL API v4
- Use GitHub GraphQL endpoint to query repository history and discussion threads.
- *Pros:* Richer query flexibility.
- *Cons:* Strictly requires personal access tokens (cannot run in unauthenticated public mode); significantly higher implementation complexity for basic repository discovery.

### Option 3: Third-Party `PyGithub` / `ghapi`
- Python client libraries for GitHub API.
- *Pros:* Pre-built SDK models.
- *Cons:* `PyGithub` is synchronous blocking; adds external dependencies; opinionated object lifecycle incompatible with our async pipeline DAG.

## Decision Rationale
We select **Option 1**: A native asynchronous `GithubIngestor` implementing `BaseIngestor` via `httpx.AsyncClient`.

Key Design Specifications:
1. **Endpoint & Queries:**
   - Base URL: `https://api.github.com/search/repositories`
   - Default queries configured from catalog: `topic:test-generation sort:updated`, `topic:mutation-testing sort:stars`, `topic:evals OR topic:llm-evaluation sort:stars`.
2. **Header Configuration:**
   - `Accept: application/vnd.github+json`
   - `X-GitHub-Api-Version: 2022-11-28`
   - `User-Agent: TrendHorizonRadar/0.1.0`
   - `Authorization: Bearer <token>` (if `GITHUB_TOKEN` is present in `Settings`).
3. **Telemetry Calculation:**
   - Engagement points calculated from stars, forks, and issues.
   - Delta time calculated from repository `pushed_at` or `created_at` against reference time.
   - Velocity calculated and attached to `engagement_metrics`.
4. **Health Check:**
   - Queries `https://api.github.com/rate_limit` or a lightweight `q=topic:test-generation&per_page=1` search.

## Consequences

### Positive
- Live extraction of repository momentum and velocity.
- Full operational symmetry between public unauthenticated runs and token-authenticated runs.
- 100% async pipeline integration without thread blocking.
- Strict type safety (`mypy --strict`) and high test coverage.

### Negative / Trade-offs
- Without `GITHUB_TOKEN`, high-frequency queries in quick succession can exhaust the 60 req/hr IP limit.
