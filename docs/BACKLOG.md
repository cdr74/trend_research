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

## Milestone 2: Source Ingestion, Telemetry & Heuristic Noise Sieve (NEXT UP)
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
- [ ] **M2-T3: Open Source Repository & Metrics Ingestor (GitHub)**
  - Implement GitHub API / GraphQL client tracking star velocity ($\Delta \text{stars}/\Delta t$), contributor counts, and issue resolution velocity.
- [ ] **M2-T4: Practitioner Publication & Media Ingestor (RSS / Atom / Web)**
  - Implement feed reader capturing engineering case studies, post-mortems, and community telemetry.
- [ ] **M2-T5: Stage 1 Noise Sieve (Rule-based Filter)**
  - Implement heuristic classifier dropping marketing buzzwords, unsubstantiated claims, and affiliate links.
  - Calculate early `heuristic_noise_score`; immediately drop records with hype $> 0.60$.
  - *Acceptance Criteria:* Stage 1 filter correctly drops synthetic benchmark claims and sponsored listicles with > 90% precision.

---

## Milestone 3: Topic Convergence, Adversarial Committee & Evaluation Pipeline
**Goal:** Implement deep fact extraction, pgvector topic clustering, cross-source corroboration, multi-lens committee review, and radar categorization.

### Stories & Tasks:
- [ ] **M3-T1: Pluggable LLM Provider Adapter**
  - Implement `LLMProvider` interface in `src/radar/providers/`.
  - Implement `GeminiProvider`, `OpenAICompatibleProvider` (Ollama/vLLM/OpenAI), and deterministic `MockProvider` for testing.
  - Implement structured output validation using Pydantic schemas.
- [ ] **M3-T2: Stage 2 Deep Extractor Agent**
  - Extract technical claims, evidence tiers, reproducible artifacts, and domain classifications from normalized signals.
  - Compute text embeddings using the pluggable provider and persist to `pgvector`.
- [ ] **M3-T3: pgvector Topic Convergence & Cross-Source Corroboration (Option 3B)**
  - Implement semantic topic clustering: link signals across distinct source channels sharing similarity $> 0.82$ to a shared `TrendTopic`.
  - Award positive consensus bonus for independent multi-source corroboration ($N_{\text{sources}} \ge 3$).
  - Detect parasitic wrappers (similarity $> 0.88$ with no distinct dataset/code) and apply automated Wrapper Penalty ($-0.20$).
- [ ] **M3-T4: Stage 3 Multi-Lens Evaluator Committee (Option 2C)**
  - Implement 3 discrete critic agents with domain governance prompts:
    1. Security & Privacy Lens (Weight: 35% - data egress boundaries, zero-trust, secret handling)
    2. Operational Feasibility Lens (Weight: 35% - seed determinism, runner footprint, integration friction)
    3. Technical Rigor Lens (Weight: 30% - empirical problem-solving vs synthetic vanity benchmarks)
  - Generate structured committee scores, risk flags, prerequisites, and critiques.
- [ ] **M3-T5: Stage 4 Radar Categorizer & Lifecycle Trajectory**
  - Synthesize committee viability, validity, and corroboration into final Radar rings (`Adopt`, `Trial`, `Assess`, `Hold`).
  - Classify lifecycle trajectory (`Emerging`, `Consolidated`, `Fading`) based on time-decayed engagement velocity.
- [ ] **M3-T6: Golden Benchmark Evaluation Test Suite**
  - Create regression benchmark with 10 high-signal verified innovations vs. 10 hype products.
  - Assert deterministic scoring thresholds.

---

## Milestone 4: Presentation, CLI & Decoupled Interactive Web Dashboard
**Goal:** Deliver flexible multi-view visualization, filtering, and automated intelligence reporting.

### Stories & Tasks:
- [ ] **M4-T1: CLI Operations Tool (`radar`)**
  - Implement CLI with commands: `radar ingest`, `radar evaluate`, `radar query`, `radar export`.
- [ ] **M4-T2: Bi-Weekly Markdown Executive Digest Generator**
  - Automated generation of `reports/YYYY-WW.md` detailing ring movements, new entries, and key skeptic findings.
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
