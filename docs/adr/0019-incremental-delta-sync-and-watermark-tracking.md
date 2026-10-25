# ADR 0019: Incremental Delta Sync and Watermark Tracking for On-Demand WSL Execution

## Status
Accepted

## Context
Rather than relying on continuous cloud-based cron schedules (which consume cloud runner quotas, poll external APIs unnecessarily, and lack localized human interaction), the engineer requires an on-demand, stateful sync workflow executable locally in WSL.

The platform must satisfy four core operational requirements:
1. **Incremental Delta Synchronization:** Running `radar sync` must only fetch and evaluate new signals published or updated since the last execution ("high-water mark").
2. **Deep Baseline Inception (365-Day Lookback):** On the initial run—or whenever a brand-new source is added—the system must automatically ingest up to 365 days of historical signals to anchor emerging trends in established knowledge.
3. **Declarative Source Extensibility:** Adding, tuning, or disabling sources must be performed directly in `data/seeds/sources.yaml` without touching application code.
4. **Frictionless State Management & Reset:** The engineer must be able to inspect, reset globally, or reset per-source watermarks effortlessly when sources are modified or re-indexed.

## Options Considered

### Option 1: Local High-Water Mark JSON State with Per-Source Timestamps (Selected)
- A persistent JSON state file (`data/.sync_state.json`) tracks:
  - Global `last_sync_at` timestamp.
  - Per-source watermark dictionary (`sources: { "<source_id>": "<ISO-timestamp>" }`).
  - Run execution history and signal counts.
- **Why this is preferred:**
  - Zero database dependency for state recovery; works seamlessly across DB restarts and offline mock runs.
  - Transparent and human-inspectable (`cat data/.sync_state.json`).
  - Trivial reset ergonomics (`radar sync --reset`, `radar sync --reset-source <id>`, or `rm data/.sync_state.json`).
  - Supports differential lookback: existing sources fetch only their delta, while brand-new sources added to `sources.yaml` automatically pull the full 365-day baseline.

### Option 2: Database-Only Watermark Table
- Store sync timestamps in a PostgreSQL `sync_watermarks` table.
- *Trade-offs:* If the local Podman database container is recreated or offline, watermarks are wiped or unreachable; cannot be inspected via simple CLI tools without a running database engine.

### Option 3: Stateless Date Flags on Every Run
- Require the user to pass `--since YYYY-MM-DD` manually on every command.
- *Trade-offs:* Burdens the engineer with remembering and tracking dates manually, leading to gaps or redundant re-ingestion.

## Decision Rationale
We implement **Option 1**:
1. **Watermark Engine (`src/radar/core/watermark.py`)**:
   - `WatermarkManager` manages `data/.sync_state.json`.
   - Default initial lookback: **365 days** (`DEFAULT_INITIAL_LOOKBACK_DAYS = 365`).
   - Provides methods: `get_watermark(source_id)`, `update_watermark(source_id, timestamp)`, `reset_all(lookback_days)`, and `reset_source(source_id, lookback_days)`.
2. **Unified Pipeline (`radar sync`) in `src/radar/presentation/cli.py`**:
   - Reads `data/seeds/sources.yaml` via `load_source_catalog()`.
   - For each enabled source, resolves its specific watermark (defaulting to 365 days ago if first run).
   - Ingests signals via arXiv, GitHub, and RSS feed collectors passing `since=watermark`.
   - Executes the 4-stage evaluation DAG (`sieve` $\to$ `extractor` $\to$ `convergence` $\to$ `evaluator` $\to$ `categorizer`).
   - Updates `web/public/radar.json` (with 2D UMAP projection) and generates the latest Markdown executive digest.
   - Updates and flushes the watermarks to `data/.sync_state.json`.

## Consequences

### Positive
- Perfect developer ergonomics in WSL: a single command (`uv run radar sync`) brings the entire intelligence database up to date.
- Zero cloud cron costs, zero unnecessary remote API polling.
- Adding a new source to `data/seeds/sources.yaml` automatically backfills 365 days of history for that source on the next sync without re-fetching all other sources.
- Comprehensive user guide documentation covering every workflow (onboarding, delta sync, catalog modification, resets, and offline testing).

### Negative / Trade-offs
- The initial 365-day baseline ingestion may take a few minutes depending on network bandwidth and API rate limits; polite throttling and batch limits (`--limit-per-source`) ensure API compliance.
