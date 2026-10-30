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

---

## Milestone 10: GitHub Pages Continuous Deployment & Release Distribution Artifacts (Completed)
**Goal:** Automate zero-install interactive radar dashboard deployment to GitHub Pages on every release and push to main, package cross-platform distribution bundles (.tar.gz and .zip) as downloadable GitHub Release assets, and preserve evaluated production data in CI.

### Stories & Tasks:
- [x] **M10-T1: Architectural Specification: GitHub Pages & Release Distribution (ADR-0025)**
  - Author and approve ADR-0025 defining continuous deployment triggers, data preservation invariants, and release artifact packaging.
  - *Acceptance Criteria:* ADR-0025 committed and indexed.
- [x] **M10-T2: Automated GitHub Pages Deployment Workflow (.github/workflows/pages.yml)**
  - Configure automated triggers: `push` to `main`, `release: [published]`, and manual `workflow_dispatch`.
  - Verify and prioritize committed `web/public/radar.json`, skipping heavy ML dependencies for sub-30-second builds while preserving mock export fallback.
  - Configure GitHub Pages build, artifact upload, and deployment steps.
  - *Acceptance Criteria:* Workflow validates data bundle and builds static assets ready for GitHub Pages hosting.
- [x] **M10-T3: Release Asset Packaging & Distribution (.github/workflows/release.yml)**
  - Extend release packaging to build both `radar-web-dashboard.tar.gz` and `radar-web-dashboard.zip` using Python `shutil.make_archive`.
  - Upload dashboard bundles alongside Python wheels and source distributions on each SemVer release tag.
  - *Acceptance Criteria:* Release workflow attaches web dashboard distribution packages directly to GitHub Releases.
- [x] **M10-T4: Documentation & Live Site Integration (README.md & docs/USER_GUIDE.md)**
  - Add GitHub Pages live link and badge in `README.md`.
  - Document zero-install online access and offline release asset extraction in `docs/USER_GUIDE.md`.
  - *Acceptance Criteria:* Documentation reflects live demo URL and distribution assets.
- [x] **M10-T5: Documentation Consolidation & Redundant Intent Spec Removal (Ref: ADR-0021)**
  - Remove redundant root-level `ai_test_engineering_radar_intent_architecture.md` superseded by `README.md`, `docs/design/architecture.md`, and `docs/adr/0021-multi-tiered-domain-relevance-and-topic-filtering.md`.
  - Update `README.md` documentation index to eliminate dead link and reference canonical system architecture and domain guardrails.
  - *Acceptance Criteria:* Redundant file removed, broken links eliminated, documentation hierarchy clean and unified.

---

## Milestone 11: Ingestion Resilience, GitHub Rate-Limit Optimization & Community Feed Integration (Completed)
**Goal:** Fix feed failures, replace defunct source streams, stabilize GitHub search pagination to eliminate unauthenticated 403 rate limits, and implement a dedicated HackerNews Algolia community collector.

### Stories & Tasks:
- [x] **M11-T1: Architectural Specification: Robust Feed Endpoints & Community Ingestion (ADR-0026)**
  - Author and approve ADR-0026 documenting feed replacements, GitHub search batch stabilization, and the Algolia community collector.
  - *Acceptance Criteria:* ADR-0026 authored and indexed in README.md.
- [x] **M11-T2: Source Catalog Endpoint Repair & Replacement (sources.yaml & data_sources.md)**
  - Fix Software Testing Weekly endpoint URL to point to `/issues/rss/`.
  - Mark decommissioned Uber Engineering Blog as disabled and introduce active Cloudflare Engineering Blog.
  - *Acceptance Criteria:* Ingestion catalog validated and unit tests pass.
- [x] **M11-T3: GitHub Ingestor Fixed Batch Pagination & Rate-Limit Protection**
  - Refactor `GithubIngestor.fetch_records` to maintain stable `per_page` request sizes and enforce `max_pages` ceiling.
  - Add rate-limit header parsing and graceful handling for 403/429 responses.
  - *Acceptance Criteria:* Unit tests prove pagination does not degrade to 1 item per request and avoids 403 errors.
- [x] **M11-T4: Dedicated HackerNews Algolia Community Collector & CLI Integration**
  - Add `SourceType.COMMUNITY` to `radar.core.models.SourceType`.
  - Implement `HnAlgoliaIngestor` in `src/radar/ingestion/community.py` supporting disjunctive queries, native timestamp filtering, and telemetry extraction.
  - Wire CLI `sync` to route `community` channels to `HnAlgoliaIngestor` and pass `keywords` to `RssFeedIngestor`.
  - *Acceptance Criteria:* Full unit test coverage with mock HTTP responses, live ingestion verified.
- [x] **M11-T5: Test Suite Verification & Ingestion Sync Validation**
  - Run `uv run pytest -v`, `uv run ruff check .`, `uv run mypy src tests`.
  - Verify sync command with real endpoints.
  - *Acceptance Criteria:* All checks pass cleanly with 100% test integrity.
- [x] **M11-T6: User Guide Ingestion Limit & Stream Batching Documentation (docs/USER_GUIDE.md)**
  - Document `--limit-per-source` parameter, default cap of 20 items, LLM token budget rationale, and deep bootstrap recipes.
  - Fix erroneous `--limit` flags in sync examples in `docs/USER_GUIDE.md` to match actual CLI syntax.
  - *Acceptance Criteria:* Documentation clearly guides operators on tuning ingestion volumes.

---

## Milestone 12: Streamlined 3-View Navigation & Interactive SVG Pan-Zoom Capabilities (Completed)
**Goal:** Deprecate the redundant Scatter Matrix view, streamline dashboard navigation to three primary perspectives (Radar Quadrant, Matrix Table, Semantic Clusters), and implement high-performance, scale-invariant SVG pan-and-zoom capabilities with floating HUD controls for dense cluster inspection.

### Stories & Tasks:
- [x] **M12-T1: Architectural Specification: View Streamlining & Pan-Zoom Interaction (ADR-0027)**
  - Author and approve ADR-0027 documenting view simplification and SVG transform pan-zoom architecture.
  - *Acceptance Criteria:* ADR-0027 authored and indexed in README.md.
- [x] **M12-T2: Reusable Zero-Dependency SVG Pan & Zoom Hook (`web/src/hooks/useZoomPan.ts`)**
  - Implement custom hook handling cursor-centered mouse wheel zooming, drag panning, bounding constraints (0.6x to 6.0x), and programmatic controls.
  - *Acceptance Criteria:* Hook exposes transform coordinates, event listeners, scale percentage, and reset functions cleanly.
- [x] **M12-T3: Pan & Zoom Integration in Radar Chart with Floating HUD Controls (`web/src/components/RadarChart.tsx`)**
  - Wrap SVG rendering in transform group and wire mouse wheel / drag interaction.
  - Render floating HUD buttons (`[+]`, `[-]`, `[Reset]`, and zoom level display).
  - Apply inverse scale factor to blip markers and labels so text remains legible and blips do not swell.
  - *Acceptance Criteria:* Operator can smoothly zoom into and pan across dense ring quadrants with 300+ items.
- [x] **M12-T4: Pan & Zoom Integration in Semantic Cluster Map (`web/src/components/ClusterMap.tsx`)**
  - Wire `useZoomPan` into ClusterMap SVG and add floating HUD controls.
  - Apply inverse scaling to cluster dots and labels.
  - *Acceptance Criteria:* Operators can zoom in on tight UMAP semantic clusters and inspect co-located entities.
- [x] **M12-T5: View Navigation Streamlining (Option A: Deprecate Scatter Matrix)**
  - Remove Scatter Matrix tab from `App.tsx` and delete `web/src/components/ScatterPlot.tsx`.
  - Streamline navigation bar to Radar Quadrant, Matrix Table, and Semantic Clusters.
  - Update `docs/USER_GUIDE.md` and verify static compilation.
  - *Acceptance Criteria:* `npm run build` succeeds with zero errors, bundle size reduced.

---

## Milestone 13: Canonical Exemplar Consolidation & Open-Source Traction Sieve (Completed)
**Goal:** Address information density and visual clutter across the radar by implementing a Stage 1 minimum traction/viability gate for open-source repositories, dynamic canonical exemplar election in Stage 4 / export with corroborating evidence aggregation, and an Executive Radar vs Full Intelligence dual-perspective toggle in the web dashboard.

### Stories & Tasks:
- [x] **M13-T1: Architectural Specification: Canonical Exemplar Consolidation & Traction Sieve (ADR-0028)**
  - Author and formalize ADR-0028 documenting the three-tiered deduplication and curation architecture.
  - *Acceptance Criteria:* ADR-0028 authored and indexed in README.md.
- [x] **M13-T2: Stage 1 Minimum Traction Gate for Open-Source Repositories (`src/radar/pipeline/noise_sieve.py`)**
  - Implement heuristic traction gate in `NoiseSieve.evaluate()` for `SourceType.GITHUB` payloads.
  - Require baseline traction (`stars >= 25` OR `velocity >= 5.0`) unless academic peer-reviewed authority is present.
  - Add rejection audit reason for insufficient open-source traction.
  - Configure via `settings.github_min_stars` (25) and `settings.github_min_velocity` (5.0).
  - Add unit tests in `tests/unit/test_noise_sieve.py`.
  - *Acceptance Criteria:* 0-star repos and unmaintained experiments rejected deterministically at Stage 1; unit tests pass.
- [x] **M13-T3: Domain Models & Database Schema for Canonical Exemplars (`models.py`, `tables.py`, `repository.py`)**
  - Add `is_canonical: bool = Field(default=True)` to `RadarItem` domain model.
  - Add `is_canonical: Mapped[bool] = mapped_column(Boolean, default=True, index=True)` to `RadarItemTable`.
  - Update repository queries and export logic to preserve canonical status.
  - *Acceptance Criteria:* `mypy --strict` passes cleanly; DB schema reflects `is_canonical` column.
- [x] **M13-T4: Stage 4 Canonical Exemplar Selection & Corroborating Evidence Aggregation (`src/radar/pipeline/categorizer.py`)**
  - Implement dynamic exemplar ranking per converged `TrendTopic` based on Ring priority, Viability, and Velocity.
  - Elect top $K$ (3–5) exemplars per topic cluster as canonical (`is_canonical = True`).
  - Mark long-tail cluster members as non-canonical (`is_canonical = False`).
  - Aggregate non-canonical tool names and URLs into the canonical exemplars' `corroborating_sources` and increment `corroboration_count`.
  - Update static bundle export in `src/radar/presentation/cli.py` to output `is_canonical`.
  - Add unit tests in `tests/unit/test_categorizer.py`.
  - *Acceptance Criteria:* Topics with dozens of blips elect top 3–5 canonical exemplars and rollup long-tail evidence cleanly.
- [x] **M13-T5: Web Dashboard Executive Radar Toggle & Velocity Filtering (`web/src/`)**
  - Update `web/src/types.ts` to include `is_canonical?: boolean`.
  - Add Executive Radar (`[★ Executive Radar (Top Exemplars)]`) vs Full Intelligence (`[🌐 All Signals]`) toggle in `App.tsx` (defaulting to Executive).
  - Filter radar items by `item.is_canonical !== false` in Executive mode.
  - Update sub-header stats display to show: "Showing X Canonical Exemplars (filtered from Y total signals)".
  - Add minimum velocity filter option in `FilterSidebar.tsx`.
  - Display rolled-up corroborating tools cleanly in `ItemDetailModal.tsx`.
  - *Acceptance Criteria:* Dashboard defaults to ~40 crisp canonical blips; operator can toggle to see all 300+ items seamlessly; `npm run build` succeeds.
- [x] **M13-T6: Test Suite Verification & Export Parity**
  - Run full test suite (`uv run pytest -v`).
  - Run `uv run ruff check .` and `uv run mypy src tests`.
  - Verify static web compilation (`npm run build`).
  - Run re-export / evaluation on corpus to update `web/public/radar.json`.
  - *Acceptance Criteria:* 100% test integrity, zero type errors, clean production bundle.
