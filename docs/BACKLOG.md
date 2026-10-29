# Product & Engineering Backlog: Trend Horizon Radar

## Project Overview & Core Parameters
- **Mission:** Autonomous intelligence platform for professionals that continuously monitors, filters, corroborates, and evaluates emerging technology trends, enforcing deterministic anti-hype penalties, multi-source topic convergence, engagement velocity tracking, and multi-lens adversarial evaluation via pluggable domain profiles.
- **Repository:** `https://github.com/cdr74/trend_research`
- **Target Runtime:** Python 3.12 managed via `uv`, Node.js 20+ for web dashboard.
- **Persistence:** Local PostgreSQL 16 + pgvector via Podman.
- **LLM Abstraction:** Pluggable Provider Interface (Google Gemini, OpenAI-compatible, Ollama/vLLM air-gapped, Offline Mock).
- **Presentation:** Decoupled static SPA (Vite + React + Tailwind + D3) deployable to GitHub Pages + Markdown executive digests.

---

## Milestone 1: Repository Baseline, Schemas & Tooling Harness (Completed)
**Goal:** Establish enterprise-grade tooling, data schema contracts, project documentation, and automated test runners.

### Stories & Tasks:
- [x] **M1-T1: Documentation Architecture & Project Inception**
  - Establish `README.md`, `docs/design/architecture.md`, `docs/BACKLOG.md`, `docs/USER_GUIDE.md`, and `GEMINI.md`/`AGENTS.md`.
  - Author foundational ADRs: ADR-0000 (Macro Architecture), ADR-0001 (Tooling), ADR-0002 (Postgres/pgvector), ADR-0003 (LLM Adapter), ADR-0004 (DAG & Schemas), ADR-0005 (Visualization).
  - *Acceptance Criteria:* All Phase 1 documentation assets created and validated.
- [x] **M1-T2: Python Project Setup & Tooling Configuration**
  - Initialize `pyproject.toml` targeting Python 3.12 using `uv`.
  - Configure `ruff` (linter & formatter), `mypy` (strict type-checking), and `pytest` with `pytest-asyncio`.
  - Configure root directory structure: `src/radar/`, `tests/`, `scripts/`, `data/`.
  - *Acceptance Criteria:* `uv sync`, `uv run ruff check .`, `uv run mypy src tests`, and `uv run pytest` pass cleanly.
- [x] **M1-T3: Pydantic v2 Core Schemas & Validation Contracts**
  - Implement `src/radar/core/models.py` with `SignalPayload`, `SignalDossier`, `EnterpriseEvaluation`, `TrendTopic`, and `RadarItem`.
  - Add JSON schema generation utility to emit `docs/schemas/` contracts.
  - Write comprehensive unit tests for schema validation and edge cases.
  - *Acceptance Criteria:* Unit tests achieve 100% coverage on core data models.
- [x] **M1-T4: Local Infrastructure via Podman Compose**
  - Create `compose.yaml` declaring PostgreSQL 16 with `pgvector` extension and persistent volume.
  - Create database bootstrap scripts and test connection harness in `src/radar/db/`.
  - *Acceptance Criteria:* `podman compose up -d` boots a healthy PostgreSQL instance with `pgvector` enabled.
- [x] **M1-T5: Continuous Integration Pipeline (.github/workflows/ci.yml)**
  - Configure GitHub Actions workflow running linting (`ruff`), type checking (`mypy`), test suite (`pytest`), and web dashboard build.
  - *Acceptance Criteria:* CI configuration adheres to remote parity requirements.

---

## Milestone 2: Source Ingestion, Telemetry & Heuristic Noise Sieve (Completed)
**Goal:** Build asynchronous multi-channel ingestion collectors, capture audience engagement telemetry, and execute Stage 1 deterministic noise filtering.

### Stories & Tasks:
- [x] **M2-T1: Ingestion Engine Contract, Registry & Telemetry Normalizer**
  - Implement `src/radar/ingestion/base.py` defining asynchronous `BaseIngestor` protocol.
  - Normalize engagement metrics (citations, reader counts, viewer data, stars/forks) and compute baseline velocity.
  - Establish curated multi-channel source catalog in `data/seeds/sources.yaml` and `docs/data_sources.md`.
  - *Acceptance Criteria:* Full test coverage for normalization formulas, protocol validation, and source registry parsing.
- [x] **M2-T2: Academic Pre-Print Ingestion Collector (arXiv / Semantic Scholar)**
  - Implement academic API client querying technical pre-prints with citation metadata.
  - Implement `ArxivIngestor` protocol compliance, polite pacing (3s delay), exponential backoff, and Atom XML normalization.
  - Wire CLI `radar ingest --sources=arxiv`.
  - *Acceptance Criteria:* Full offline unit test coverage with fixtures, live connectivity validated, zero added dependencies. (Ref: ADR-0006)
- [x] **M2-T3: Open Source Repository & Metrics Ingestor (GitHub)**
  - Implement GitHub API search client tracking star velocity ($\Delta \text{stars}/\Delta t$), forks, and issue telemetry.
  - Implement `GithubIngestor` protocol compliance, public zero-token fallback, optional `GITHUB_TOKEN` support, and rate limit backoff.
  - *Acceptance Criteria:* Full unit test coverage with fixtures, live connectivity validated, engagement velocity calculated. (Ref: ADR-0007)
- [x] **M2-T4: Practitioner Publication & Media Ingestor (RSS / Atom / Web)**
  - Implement feed reader capturing engineering case studies, post-mortems, and community telemetry.
  - Implement `RssFeedIngestor` supporting dual RSS 2.0 / Atom 1.0 parsing, RFC 2822 / ISO 8601 date parsing, and HTML text stripping.
  - *Acceptance Criteria:* Full test suite with RSS/Atom fixtures, live engineering blog ingestion verified. (Ref: ADR-0008)
- [x] **M2-T5: Stage 1 Noise Sieve (Rule-based Filter)**
  - Implement heuristic classifier dropping marketing buzzwords, unsubstantiated claims, and affiliate links.
  - Calculate early `heuristic_noise_score`; immediately drop records with hype $> 0.60$.
  - Integrated into pipeline with `NoiseFilterResult` and `QualifiedSignal` promotion.
  - *Acceptance Criteria:* Stage 1 filter correctly drops synthetic benchmark claims and sponsored listicles with > 90% precision on golden benchmark suite. (Ref: ADR-0009)

---

## Milestone 3: Topic Convergence, Adversarial Committee & Evaluation Pipeline (Completed)
**Goal:** Implement deep fact extraction, pgvector topic clustering, cross-source corroboration, multi-lens committee review, and radar categorization.

### Stories & Tasks:
- [x] **M3-T1: Pluggable LLM Provider Adapter**
  - Implement `LLMProvider` interface in `src/radar/providers/`.
  - Implement `AgyCliProvider` bridge for zero-cost local execution via `agy` CLI on WSL.
  - Implement `GeminiProvider`, `OpenAICompatProvider` (Ollama/vLLM/OpenAI), and deterministic `MockProvider` for testing.
  - Implement structured output validation using Pydantic schemas and JSON repair fallback.
  - *Acceptance Criteria:* Full test coverage across all adapters, verified live on local WSL `agy` CLI and mock transports. (Ref: ADR-0010)
- [x] **M3-T2: Stage 2 Deep Extractor Agent**
  - Extract technical claims, evidence tiers, reproducible artifacts, and domain classifications from normalized signals.
  - Compute text embeddings using the pluggable provider and persist to `pgvector`.
  - Wire into CLI `radar evaluate` for batch processing of pending signals.
  - *Acceptance Criteria:* Full test coverage with MockProvider, strict Pydantic v2 validation contracts, deterministic vector generation. (Ref: ADR-0011)
- [x] **M3-T3: pgvector Topic Convergence & Cross-Source Corroboration (Option 3B)**
  - Implement semantic topic clustering: link signals across distinct source channels sharing similarity >= threshold (default 0.82) to a shared `TrendTopic`.
  - Configurable similarity and penalty thresholds via `Settings`.
  - Autonomous LLM topic synthesis across clustered dossiers (`SynthesizedTopic`).
  - Award positive consensus bonus (+0.25) for independent multi-source corroboration ($N_{\text{sources}} \ge 3$).
  - Detect parasitic wrappers (similarity >= 0.88 with no distinct dataset/code) and apply automated Wrapper Penalty (-0.20).
  - *Acceptance Criteria:* Full test coverage for cosine similarity, topic synthesis, wrapper penalties, and consensus bonus. (Ref: ADR-0012)
- [x] **M3-T4: Stage 3 Multi-Lens Evaluator Committee (Option 2C)**
  - Implement 3 discrete critic lenses with domain governance prompts:
    1. Security & Privacy Lens (Weight: 35% - data egress boundaries, zero-trust, secret handling)
    2. Operational Feasibility Lens (Weight: 35% - seed determinism, runner footprint, integration friction)
    3. Technical Rigor Lens (Weight: 30% - empirical problem-solving vs synthetic vanity benchmarks)
  - Generate structured committee scores, risk flags, prerequisites, and critiques in a single multi-perspective turn (Option B).
  - Deterministic composite viability formula ($E_v = 0.35 \cdot S_{\text{sec}} + 0.35 \cdot S_{\text{ops}} + 0.30 \cdot S_{\text{tech}}$) with configurable weights.
  - Wire into CLI `radar evaluate` and persistence layer.
  - *Acceptance Criteria:* Full unit test coverage with MockProvider, exact weight calculation verification, and risk flag auditing. (Ref: ADR-0013)
- [x] **M3-T5: Stage 4 Radar Categorizer & Lifecycle Trajectory**
  - Synthesize committee viability, validity, and corroboration into final Radar rings (`Adopt`, `Trial`, `Assess`, `Hold`).
  - Classify lifecycle trajectory (`Emerging`, `Consolidated`, `Fading`) based on time-decayed engagement velocity and corroboration.
  - Compute deterministic validity score ($S_v$) and composite hype score ($H = 1.0 - S_v$) with anti-hype deductions and engineering bonuses.
  - Wire into CLI `radar evaluate`, `radar query`, and `radar export` with JSON/CSV export support.
  - *Acceptance Criteria:* Full unit test coverage for ring decisions, lifecycle trajectories, and score bounds. (Ref: ADR-0014)
- [x] **M3-T6: Golden Benchmark Evaluation Test Suite**
  - Curate 20-item regression benchmark (10 genuine innovations across arXiv, GitHub, RSS vs 10 hype/wrapper products) in `data/fixtures/golden_benchmark.json`.
  - Execute end-to-end 4-stage pipeline DAG and assert strict acceptance gates.
  - Assert 100% recall (0 genuine innovations in Hold) and 0% false positives (10/10 hype products dropped or quarantined to Hold).
  - *Acceptance Criteria:* Full offline integration test suite passing cleanly with deterministic providers. (Ref: ADR-0015)

---

## Milestone 4: Presentation, CLI & Decoupled Interactive Web Dashboard (Completed)
**Goal:** Deliver flexible multi-view visualization, filtering, and automated intelligence reporting.

### Stories & Tasks:
- [x] **M4-T1: CLI Operations Tool (`radar`)**
  - Implement CLI with commands: `radar ingest`, `radar evaluate`, `radar query`, `radar export`, `radar inspect`.
  - JSON and CSV export formats, ring/trajectory querying, and detailed item dossier inspection.
  - *Acceptance Criteria:* Full CLI unit and integration test coverage across all subcommands. (Ref: ADR-0014, ADR-0016)
- [x] **M4-T2: Bi-Weekly Markdown Executive Digest Generator (`radar report`)**
  - Automated generation of Markdown executive intelligence digest detailing ring distributions, trajectory movements, new entries, skeptic critique highlights, and top recommendations.
  - Database offline safety guard: halts if DB unreachable without creating offline report unless `--mock` is explicitly passed.
  - *Acceptance Criteria:* Dedicated Markdown generator unit tests and CLI integration tests passing. (Ref: ADR-0016)
- [x] **M4-T3: JSON Data Bundle Exporter (`radar.json`)**
  - Standardized `RadarData` JSON schema envelope with metadata, rings, categories, and item dossiers.
  - 2D UMAP non-linear manifold projection engine (`src/radar/presentation/projection.py`) with SVD PCA fallback.
  - *Acceptance Criteria:* UMAP projection unit tests and export integration tests passing. (Ref: ADR-0017)
- [x] **M4-T4: Interactive Web Radar Dashboard (Vite + React + Tailwind)**
  - Decoupled `web/` application with instant multi-criteria sidebar filters and free-format token Omnibar:
    - Ring filter (Adopt/Trial/Assess/Hold)
    - QE Pillar filter (1-6)
    - Evidence Tier filter
    - Banking Gate / Risk Tag filters
    - Hype / Viability score range sliders
    - Smart search omnibar with token parsing (`ring:`, `category:`, `tier:`, `viability:>X`, `hype:<Y`, `risk:`)
  - 4 interactive view modes:
    1. **Radar View:** Polar radar with 4 rings, quadrant categories, and zoomable interactive blips.
    2. **Matrix View:** Data grid with sortable columns and expandable skeptic critique dossiers.
    3. **Scatter Matrix:** Interactive Hype vs Viability scatter plot with quadrant analysis.
    4. **Semantic Cluster View:** 2D spatial canvas rendering UMAP projection coordinates.
  - *Acceptance Criteria:* Static web bundle builds cleanly (`npm run build`) with zero TypeScript errors. (Ref: ADR-0005, ADR-0017)
- [x] **M4-T5: Static Build & GitHub Pages Workflow**
  - Configured automated deployment workflow (`.github/workflows/pages.yml`) publishing the static dashboard bundle to GitHub Pages.
  - *Acceptance Criteria:* Pages deployment workflow with artifact upload and deploy stages. (Ref: ADR-0017)

---

## Milestone 5: Continuous Delivery, Release & Ops Automation (Completed)
- [x] **M5-T1: Automated SemVer Release Tagging & Changelog Automation**
  - Integrated Google Release Please (`.release-please-config.json`, `.release-please-manifest.json`, `CHANGELOG.md`).
  - Automated Release PR generation on pushes to `main` analyzing Conventional Commits.
  - Automated packaging of Python wheels/sdists (`uv build`) and static web dashboard archive (`radar-web-dashboard.tar.gz`) uploaded to GitHub Releases on PR merge.
  - *Acceptance Criteria:* Release Please GitHub Actions workflow configured and validated. (Ref: ADR-0018)
- [x] **M5-T2: On-Demand Incremental Sync & Watermark Pipeline**
  - Local-first delta synchronization (`radar sync`) eliminating cloud cron schedules per user operational requirements.
  - Stateful `WatermarkManager` in `src/radar/core/watermark.py` persisting to `data/.sync_state.json`.
  - Configurable lookback buffer (`--days`, defaulting to 365-day initial baseline load to establish historical trend context).
  - Source-level watermark resets (`--reset-source <id>`) and global state resets (`--reset`).
  - Automated integration with declarative source catalog in `data/seeds/sources.yaml`.
  - Single-command orchestration running incremental multi-channel ingestion, noise filtering, and 4-stage evaluation DAG.
  - *Acceptance Criteria:* Full unit test coverage for watermark manager and CLI sync command, verified state reset and incremental ingestion flows. (Ref: ADR-0019)
- [x] **M5-T3: Interactive Database Container Lifecycle & User Consent Startup**
  - Probe database health in `src/radar/db/container.py` before executing persistence flows.
  - Prompt user with interactive Rich confirmation when PostgreSQL is offline to start via `podman compose up -d`.
  - Asynchronous container startup, health poll, and schema bootstrap via `init_db()`.
  - Non-interactive / CI / `--mock` bypass safety to avoid hanging headless processes.
  - Added CLI overrides `--auto-start-db` and `--no-db` across `sync`, `evaluate`, and `query`.
  - *Acceptance Criteria:* Full unit test coverage for container probe and interactive consent flow in CLI. (Ref: ADR-0020)
- [x] **M5-T4: Web Dashboard Server Orchestration & Automatic Verification**
  - Add first-class `radar ui` and `radar serve` commands to verify prerequisites, auto-install missing `web/node_modules` via `npm ci`, validate static data bundle, and launch Vite dev server.
  - Automatically detect active dashboard server during `radar sync`, with `--ui` flag to start web server upon sync completion.
  - Fix `ensure_db_running` to guarantee idempotent schema initialization (`init_db()`) whenever PostgreSQL is already running.
  - Reorganize `docs/USER_GUIDE.md` with top-level Quick Reference Cheatsheet for instant multi-project operational reference.
  - *Acceptance Criteria:* Full unit test coverage for `radar ui`, `radar serve`, `sync --ui`, and database schema auto-init.

---

## Milestone 6: Multi-Tiered Domain Relevance & Noise Immunity (Completed)
**Goal:** Replace fragile substring keyword filtering with a 3-tier defense-in-depth domain relevance engine across ingestion, Stage 1 noise sieving, and Stage 2 deep extraction.

### Stories & Tasks:
- [x] **M6-T1: Architectural Specification: Multi-Tiered Domain Relevance (ADR-0021)**
  - Author and approve ADR-0021 establishing the 3-tier defense-in-depth relevance architecture.
  - Refine seed source catalog in `data/seeds/sources.yaml` and `docs/data_sources.md` (add verified `llm-red-teaming` and `property-based-testing`, patch HTTP 422 queries, purge low-signal sources).
  - *Acceptance Criteria:* ADR-0021 committed, catalog validated via source loader.
- [x] **M6-T2: Tier 1 Ingestion Boundary RelevanceFilter Engine**
  - Implement `RelevanceFilter` with compiled token-boundary regexes, compound requirement rules (co-occurrence of generic terms with SE qualifiers), and negative exclusion rules.
  - Integrate `RelevanceFilter` into `RssFeedIngestor` to replace naive `_matches_keywords`.
  - *Acceptance Criteria:* 100% unit test coverage, zero false-positive substring matches (e.g., `"ai"` in `"email"`, `"test"` in `"fastest"`).
- [x] **M6-T3: Tier 2 Stage 1 Heuristic Domain Relevance Scoring (`NoiseSieve`)**
  - Add domain relevance evaluation to `NoiseSieve` in `src/radar/pipeline/noise_sieve.py`.
  - Implement dual-drop threshold (`noise_score` ≤ 0.60 and `domain_relevance_score` ≥ 0.35).
  - Add financial enterprise red flags (testing in production on live systems, autonomous un-audited merges) and adequacy evidence credits.
  - *Acceptance Criteria:* Unit tests prove high-credibility non-SE papers (e.g. pure math, astrophysics) are dropped before LLM extraction.
- [x] **M6-T4: Tier 3 Stage 2 Deep Extractor Dual-Track & Out-of-Domain Guardrail**
  - Extend `ExtractedInnovation` model with `track: TrackType`, `is_qe_relevant: bool`, and `adequacy_evidence: list[str]`.
  - Update system prompt in `DeepExtractor` to classify out-of-domain signals and detect Dual-Track innovations.
  - Update presentation layer and Web UI with Dual-Track query tokens (`track:testing`, `track:evaluation`).
  - *Acceptance Criteria:* End-to-end unit and integration tests passing cleanly across all tiers.
- [x] **M6-T5: Live Web Dashboard Synchronization & Dual-Track UI Switcher**
  - Synchronize live PostgreSQL signals into web bundle automatically on `radar ui` startup.
  - Add Dual-Track switcher tab bar to Web UI header (All Tracks, Software Testing, AI Evaluation) with reactive item counts.
  - Propagate track field in bundle exports and add Track column to `TableView` and `ItemDetailModal`.
  - Fix test runner export clobbering to isolate mock sync runs from production dashboard bundles.
  - *Acceptance Criteria:* Web dashboard reflects all 23 live database signals without stale mock cache fallback.

---

## Milestone 7: Precision Radar Ranking & Gated Categorization (Completed)
**Goal:** Address bimodal radar skew (20 Adopt, 3 Hold, 0 Assess, 0 Trial) by establishing multi-gated deterministic ring criteria, protecting practitioner post-mortems from wrapper penalties, and upgrading mock embeddings.

### Stories & Tasks:
- [x] **M7-T1: Architectural Specification: Multi-Gated Radar Categorization (ADR-0022)**
  - Author and approve ADR-0022 establishing lifecycle-gated `Adopt`, widened `Trial` and `Assess` bands, and practitioner post-mortem protection.
  - Amend ADR-0014 to reference multi-gated decision matrix.
  - *Acceptance Criteria:* ADR-0022 committed and integrated into architecture registry.
- [x] **M7-T2: Configurable Multi-Gated Thresholds & Precision RadarCategorizer**
  - Update `Settings` with calibrated thresholds: `ring_adopt_min_viability = 0.80`, `ring_adopt_max_hype = 0.30`, `ring_trial_min_viability = 0.70`, `ring_trial_max_hype = 0.40`, `ring_assess_min_viability = 0.45`, `stars_consolidated_threshold = 500.0`.
  - Refactor `RadarCategorizer.determine_ring` to accept `lifecycle_stage` and strictly enforce `LifecycleStage.CONSOLIDATED` for `Adopt`.
  - Re-route high-viability `EMERGING` technologies into `Trial` and exploratory items into `Assess`.
  - *Acceptance Criteria:* Unit tests verify correct ring routing across consolidated, emerging, and fading lifecycle states.
- [x] **M7-T3: Topic Convergence Post-Mortem Protection & Pseudo-Orthogonal Mock Embeddings**
  - Update `TopicConvergenceEngine` to exempt `EvidenceTier.ENGINEERING_POST_MORTEM` from wrapper deductions.
  - Upgrade `MockLLMProvider.embed_text` with deterministic pseudo-orthogonal unit vectors based on text hash to eliminate artificial 1.0 cosine similarity clustering.
  - *Acceptance Criteria:* Unit tests prove distinct mock signals generate varying similarity scores, and post-mortems retain valid standing.
- [x] **M7-T4: End-to-End Test Suite Parity & Static Data Bundle Re-Export**
  - Update unit and golden benchmark integration tests to match new multi-gated categorizer behavior.
  - Re-run pipeline categorization and export re-ranked radar items to `web/public/radar.json`.
  - Verify static web build and test suite pass with 100% compliance.
  - *Acceptance Criteria:* Full CI test suite passes cleanly, `radar.json` presents a balanced ThoughtWorks distribution.

---

## Milestone 8: Dynamic Bounded Topic Convergence & Theme Attribution (Completed)
**Goal:** Prevent ecosystem fragmentation by clustering related tools into cohesive dynamic themes (bounded below 10–12 active themes) and attributing first-class theme badges across data models, exports, and web UI.

### Stories & Tasks:
- [x] **M8-T1: Architectural Specification: Dynamic Bounded Topic Convergence (ADR-0023)**
  - Author and approve ADR-0023 establishing dynamic theme convergence, topic centroid matching, and a maximum bound of 10–12 active themes.
  - *Acceptance Criteria:* ADR-0023 documented with concrete clustering parameters and trade-offs.
- [x] **M8-T2: Calibrated Theme Convergence & Bounded Centroid Clustering Engine**
  - Update `Settings` with `topic_convergence_threshold = 0.65` and `max_dynamic_themes = 12`.
  - Refactor `TopicConvergenceEngine` to cluster against running topic centroids and iteratively condense clusters if count exceeds 12.
  - Weight core technique and problem claims over repository names in `DeepExtractor.extract()`.
  - *Acceptance Criteria:* Unit tests prove tools exploring the same technique (e.g. mutation testing across Java, TS, PHP, Python) converge into a single shared topic.
- [x] **M8-T3: First-Class Theme Attribution in Core Models, Persistence & Export**
  - Add `topic_name: str | None` to `RadarItem` and `RadarItemTable`.
  - Export `topic_name` in `radar.json` bundle.
  - *Acceptance Criteria:* DB migrations and repository methods persist topic names cleanly.
- [x] **M8-T4: Web Dashboard Theme Tagging, Filtering & Omnibar Search**
  - Display dynamic theme pill badges in `TableView` and `ItemDetailModal`.
  - Add Omnibar search filter `theme:<name>` and Theme facet to `FilterSidebar`.
  - Re-export static bundle and verify web build.
  - *Acceptance Criteria:* Static web bundle compiles with zero TypeScript errors and surfaces theme groupings.

---

## Milestone 9: Radar View Ergonomics, Deterministic Blip Layout & Spec-Model Coverage (Completed)
**Goal:** Deliver spreadsheet-grade per-column filtering and sorting, expand radar viewports to eliminate label clipping, make blip layout 100% deterministic (zero hopping during filter changes), clean up scatter plot text collisions, and ingest canonical property-based testing tools to populate the "Spec & Model" pillar.

### Stories & Tasks:
- [x] **M9-T1: Architectural Specification: View Ergonomics, Determinism & Domain Coverage (ADR-0024)**
  - Document UX ergonomics, deterministic hash positioning algorithm, and Spec & Model source integration in ADR-0024.
  - *Acceptance Criteria:* ADR-0024 approved by operator.
- [x] **M9-T2: Matrix Table Per-Column Sort & Filter Controls**
  - Implement column header click sorting (asc/desc/reset) with custom comparators for rings, trajectories, and scores in `TableView.tsx`.
  - Add integrated secondary filter row for discrete dropdowns (`Track`, `Theme`, `Pillar`, `Ring`, `Trajectory`, `Evidence Tier`) and search inputs.
  - *Acceptance Criteria:* Table supports multi-parameter filtering and responsive sorting across all columns.
- [x] **M9-T3: Viewport Padding & Deterministic Radar Blip Layout**
  - Expand `RadarChart` viewBox with perimeter padding (`viewBox="-60 -60 920 920"`) and tune label text anchors to eliminate truncation.
  - Replace transient array index with deterministic FNV-1a item hash for static blip spatial coordinates.
  - *Acceptance Criteria:* Filtering or searching preserves exact blip positions without hopping.
- [x] **M9-T4: Scatter Matrix Collision Resolution & Interactive Focus**
  - Render crisp glowing dots by default, hiding static text collisions in `ScatterPlot.tsx`.
  - Display full labels and floating inspection cards on hover/selection, with an optional "Show Labels" header toggle.
  - *Acceptance Criteria:* Dense clusters display cleanly with zero text overlap.
- [x] **M9-T5: Spec & Model Tool Ingestion & Dynamic Theme Convergence**
  - Ingest canonical property-based and spec-driven testing frameworks (`HypothesisWorks/hypothesis`, `schemathesis/schemathesis`, `dubzzz/fast-check`).
  - Run Stage 1–4 pipeline to synthesize a 7th dynamic theme: `Model-Based & Property-Driven Testing` under pillar `Spec & Model`.
  - Re-export `radar.json` and verify all 6 pillars have active blips.
  - *Acceptance Criteria:* `radar.json` contains active blips across all 6 QE pillars; web dashboard compiles cleanly.
