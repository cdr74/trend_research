# Product & Engineering Backlog: AI Test Engineering Horizon Radar

## Project Overview & Core Parameters
- **Mission:** Autonomous intelligence engine filtering, evaluating, and clustering SDLC and Quality Engineering (QE) innovations with adversarial anti-hype skepticism and banking enterprise viability scoring.
- **Repository:** `https://github.com/cdr74/trend_research`
- **Target Runtime:** Python 3.12 managed via `uv`, Node.js 20+ for web dashboard.
- **Persistence:** Local PostgreSQL 16 + pgvector via Podman.
- **LLM Abstraction:** Pluggable Provider Interface (Google Gemini, OpenAI-compatible, Ollama/vLLM air-gapped, Offline Mock).
- **Presentation:** Decoupled static SPA (Vite + React + Tailwind + D3) deployable to GitHub Pages + Markdown executive digests.

---

## Milestone 1: Repository Baseline, Schemas & Tooling Harness (Current)
**Goal:** Establish enterprise-grade tooling, data schema contracts, project documentation, and automated test runners.

### Stories & Tasks:
- [x] **M1-T1: Documentation Architecture & Project Inception**
  - Establish `README.md`, `docs/design/architecture.md`, `docs/BACKLOG.md`, `docs/USER_GUIDE.md`, and `GEMINI.md`/`AGENTS.md`.
  - Author foundational ADRs: ADR-0001 (Tooling), ADR-0002 (Postgres/pgvector), ADR-0003 (LLM Adapter), ADR-0004 (DAG & Schemas), ADR-0005 (Visualization).
  - *Acceptance Criteria:* All Phase 1 documentation assets created and validated.
- [x] **M1-T2: Python Project Setup & Tooling Configuration**
  - Initialize `pyproject.toml` targeting Python 3.12 using `uv`.
  - Configure `ruff` (linter & formatter), `mypy` (strict type-checking), and `pytest` with `pytest-asyncio`.
  - Configure root directory structure: `src/radar/`, `tests/`, `scripts/`, `data/`.
  - *Acceptance Criteria:* `uv sync`, `uv run ruff check .`, `uv run mypy src tests`, and `uv run pytest` pass cleanly.
- [x] **M1-T3: Pydantic v2 Core Schemas & Validation Contracts**
  - Implement `src/radar/core/models.py` with `SignalPayload`, `SignalDossier`, `EnterpriseEvaluation`, and `RadarItem`.
  - Add JSON schema generation utility to emit `docs/schemas/signal.schema.json`.
  - Write comprehensive unit tests for schema validation and edge cases.
  - *Acceptance Criteria:* Unit tests achieve 100% coverage on core data models.
- [x] **M1-T4: Local Infrastructure via Podman Compose**
  - Create `compose.yaml` declaring PostgreSQL 16 with `pgvector` extension and persistent volume.
  - Create database bootstrap scripts and test connection harness in `src/radar/db/`.
  - *Acceptance Criteria:* `podman compose up -d` boots a healthy PostgreSQL instance with `pgvector` enabled.
- [x] **M1-T5: Continuous Integration Pipeline (.github/workflows/ci.yml)**
  - Configure GitHub Actions workflow running linting (`ruff`), type checking (`mypy`), and test suite (`pytest`) on push/PR.
  - *Acceptance Criteria:* CI configuration adheres to remote parity requirements.

---

## Milestone 2: Source Ingestion & Heuristic Noise Sieve
**Goal:** Build asynchronous ingestion collectors and Stage 1 deterministic noise filter.

### Stories & Tasks:
- [ ] **M2-T1: Ingestion Engine Contract & Base Class**
  - Implement `src/radar/ingestion/base.py` defining asynchronous `BaseIngestor` protocol.
  - Add payload normalization, rate-limiting, and error handling.
- [ ] **M2-T2: arXiv cs.SE Ingestion Collector**
  - Implement arXiv API client querying `cs.SE` (Software Engineering) and related categories.
  - Filter by keywords (mutation testing, test generation, LLM evaluation, agentic testing).
- [ ] **M2-T3: GitHub Repository & Metrics Ingestor**
  - Implement GitHub API / GraphQL client tracking star velocity, commit frequency, issue-to-resolution ratio, and open licenses.
- [ ] **M2-T4: Curated RSS & Engineering Blog Ingestor**
  - Implement RSS/Atom feed reader for Tier-1 engineering post-mortems and practitioner blogs.
- [ ] **M2-T5: Stage 1 Noise Sieve (Rule-based Filter)**
  - Implement heuristic classifier dropping marketing buzzwords, unsubstantiated claims, and affiliate links.
  - Calculate early `heuristic_noise_score`; immediately drop records with hype $> 0.60$.
  - *Acceptance Criteria:* Stage 1 filter correctly filters out synthetic benchmark claims and sponsored listicles with > 90% precision.

---

## Milestone 3: Adversarial LLM Multi-Agent Evaluation Pipeline
**Goal:** Implement deep fact extraction, adversarial banking skeptic review, and radar categorization.

### Stories & Tasks:
- [ ] **M3-T1: Pluggable LLM Provider Adapter**
  - Implement `LLMProvider` interface in `src/radar/providers/`.
  - Implement `GeminiProvider`, `OpenAICompatibleProvider` (Ollama/vLLM/OpenAI), and deterministic `MockProvider` for testing.
  - Implement structured output validation using Pydantic schemas.
- [ ] **M3-T2: Stage 2 Deep Extractor Agent**
  - Extract technical claims, evidence tiers, reproducible artifacts, and domain pillar classifications from normalized signals.
  - Compute text embeddings using the pluggable provider and persist to `pgvector`.
- [ ] **M3-T3: Stage 3 Multi-Persona Adversarial Committee (Option 2C)**
  - Implement 3 discrete critic agents with banking-grade constraint prompts:
    1. CISO / Security Architect (Weight: 35% - data egress, air-gapped readiness, secret leakage)
    2. CI/CD Platform Architect (Weight: 35% - seed determinism, runner footprint, flaky isolation)
    3. Quality Engineering Director (Weight: 30% - real defect discovery vs vanity benchmarks)
  - Generate structured committee scores, risk flags, prerequisites, and critiques.
- [ ] **M3-T4: Stage 4 Radar Categorizer & Wrapper Detection (Option 3B)**
  - Synthesize committee viability and validity scores into final Radar rings (`Adopt`, `Trial`, `Assess`, `Hold`).
  - Execute `pgvector` cosine similarity query against existing dossiers; apply automated Wrapper Penalty ($-0.20$) if similarity $> 0.88$ with no distinct benchmark.
- [ ] **M3-T5: Golden Benchmark Evaluation Test Suite**
  - Create regression benchmark with 10 high-signal verified papers vs. 10 hype products.
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
