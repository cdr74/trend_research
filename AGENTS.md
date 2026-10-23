# AGENTS.md / GEMINI.md - Agent Directives & Engineering Standards

## 1. Project Overview
The **AI Test Engineering Horizon Radar** is an autonomous intelligence pipeline that ingests, filters, evaluates, and clusters SDLC and Quality Engineering (QE) innovations. It enforces deterministic anti-hype penalties and banking enterprise viability scoring.

## 2. Engineering Standards & Strict Protocol
1. **Never Take Shortcuts:** Strictly adhere to test-driven and backlog-driven execution. Every code change must trace to a task in `docs/BACKLOG.md` and an accepted Architecture Decision Record (`docs/adr/`).
2. **Type Safety & Linting:** Strict typing (`mypy --strict`) and Ruff formatting/linting are mandatory. Code with type errors or lint warnings will fail CI.
3. **Test-First Discipline:** Write unit and integration tests alongside all implementations. Tests must run deterministically without internet dependencies (use mock providers and fixtures).
4. **Synchronized Commits:** Every commit must follow Conventional Commits and reference the relevant ADR and backlog story (e.g., `feat(models): implement Pydantic v2 signal schemas (Ref: ADR-0004, Backlog M1-T3)`).

## 3. Essential Commands & Workflows
- **Environment Sync:** `uv sync`
- **Lint & Format:** `uv run ruff check .` and `uv run ruff format .`
- **Type Check:** `uv run mypy src tests`
- **Execute Test Suite:** `uv run pytest -v`
- **Start Local DB:** `podman compose up -d`
- **Run Pipeline in Mock Mode:** `RADAR_LLM_PROVIDER=mock uv run radar evaluate`

## 4. Key Architectural Boundaries
- `src/radar/core/`: Immutable domain models, Pydantic v2 schemas, configuration. Zero dependencies on external providers or storage.
- `src/radar/db/`: PostgreSQL + pgvector persistence via SQLAlchemy 2.0 (asyncio). All queries are asynchronous.
- `src/radar/providers/`: Pluggable LLM interfaces implementing `LLMProvider`. Providers must handle structured JSON outputs and fallback gracefully.
- `src/radar/pipeline/`: 4-stage Directed Acyclic Graph (DAG) executing discrete stage logic.
- `src/radar/presentation/`: Decoupled serialization, CLI commands, and Markdown digest reporting.
- `web/`: Decoupled Vite + React + TypeScript web application.
