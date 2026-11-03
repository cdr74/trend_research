# AGENTS.md - Project Directives & Verification Standards

## 1. Execution Protocol & Phase Gates

### Phase 1: Architectural Deliberation & Specification
- When exploring, planning, or designing, deliverables are strictly limited to documentation: an Architecture Decision Record in `docs/adr/` or task specifications in `docs/BACKLOG.md`.
- **Constraint:** Deliverables are strictly limited to `docs/adr/` or `docs/BACKLOG.md`. Do not create or edit files in `src/`, `tests/`, or `web/` during this phase. Wait for explicit user confirmation before writing implementation code.
- **Empirical Calibration Sanction:** When designing heuristics, thresholds, or classifications, operators and agents are expected to run non-mutating, read-only data probes (e.g. querying local PostgreSQL, running scratch CLI inspect commands, or checking dataset distributions) to ground decisions in empirical data before locking an ADR. Any ADR proposing numerical thresholds or filter rules must cite observed distribution percentiles justifying those choices.

### Phase 2: Autonomous Implementation
- Once an ADR or specification is explicitly approved, execute implementation with full autonomy across code and test suites.
- Adhere strictly to the agreed data structures, interfaces, and boundary constraints outlined in the referenced ADR.
- Run tests and static analysis continuously until all local validation checks pass cleanly.

---

## 2. Essential Commands & Workflows

### Backend (Python via `uv`)
- **Environment Sync:** `uv sync`
- **Lint & Auto-format:** `uv run ruff check --fix .` && `uv run ruff format .`
- **Strict Type Check:** `uv run mypy src tests`
- **Test Suite:** `uv run pytest -v`
- **Local DB Infrastructure:** `podman compose up -d`
- **Mock Pipeline Run:** `RADAR_LLM_PROVIDER=mock uv run radar evaluate`

### Frontend (`web/` via `npm`)
- **Install Dependencies:** `cd web && npm ci`
- **Type Check & Build:** `cd web && npm run build`

---

## 3. Engineering Constraints & Invariants

- **Test Integrity:** All tests must run deterministically and pass offline without external network dependencies. Use local fixtures, database test instances, and mock providers.
- **Non-Degenerate Test Doubles:** Mocks simulating mathematical, embedding, or scoring components must never return uniform scalars or collinear vectors. They must generate deterministic pseudo-entropy (e.g. input-hashing across a unit hypersphere) so test suites exercise realistic variance and catch clustering bugs.
- **Type Rigor:** Full compliance with `mypy --strict`. No untyped public functions, bare `Any` types, or silenced type errors without documented justification.
- **Async Database Layer:** All operations within `src/radar/db/` must use SQLAlchemy 2.0 async conventions (`async with`, `select()`, `await session.execute()`).
- **Core Decoupling:** Domain models and schemas in `src/radar/core/` must remain pure Pydantic v2 models with zero dependencies on persistence layers (`src/radar/db/`) or external network clients (`src/radar/providers/`).
- **Taxonomic Immutability:** Core domain classifications (e.g. `QECategory` pillars) represent an entity's intrinsic function and are immutable once extracted. High-level clusters, topics, or themes are strictly associational references and must never overwrite an entity's primary classification.
- **Scale-Density by Default:** All UI visual components must be specified and verified to remain legible, responsive, and spatially stable under $10\times$ volume ($N \ge 300$). Spatial blip positioning must rely on invariant item identity hashes rather than transient array indices.
- **Traceable Commits:** All git commits must adhere to Conventional Commits and explicitly reference the corresponding ADR and Backlog task ID:
  `feat(domain): implement signal scoring schemas (Ref: ADR-0004, Backlog M1-T3)`
