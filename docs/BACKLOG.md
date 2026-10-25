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

## Milestone 4: Presentation, CLI & Decoupled Interactive Web Dashboard (IN PROGRESS)
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
- [ ] **M4-T3: JSON Data Bundle Exporter (`radar.json`)**
  - Export complete evaluated corpus with 2D UMAP projection coordinates for semantic clustering.
- [ ] **M4-T4: Interactive Web Radar Dashboard (Vite + React + Tailwind + D3)**
  - Scaffold `web/` application with instant multi-criteria sidebar filters:
    - Ring filter (Adopt/Trial/Assess/Hold)
    - QE Pillar filter (1-6)
    - Evidence Tier filter
    - Banking Gate / Risk Tag filters
    - Hype / Viability score range sliders
  - Implement 4 interactive view modes:
    1. **Radar View:** 4-quadrant interactive radar with zoomable blips.
    2. **Matrix View:** Data grid with sortable columns and expandable skeptic critique dossiers.
    3. **Scatter Matrix:** Interactive Hype vs Viability scatter plot.
    4. **Semantic Cluster View:** 2D canvas/SVG projection of tool embeddings.
- [ ] **M4-T5: Static Build & GitHub Pages Workflow**
  - Automated build and deploy workflow publishing the static dashboard to GitHub Pages.

---

## Milestone 5: Continuous Delivery, Release & Ops Automation
- [ ] Automated SemVer release tagging and changelog generation.
- [ ] Scheduled cron workflow for periodic automated ingestion and evaluation runs.
