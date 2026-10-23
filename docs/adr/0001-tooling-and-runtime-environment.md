# ADR 0001: Tooling and Runtime Environment (Python 3.12, uv, Ruff, Pytest)

## Status
Accepted

## Context
The AI Test Engineering Horizon Radar requires a robust, reproducible, and performant developer environment. The system will handle asynchronous data ingestion (arXiv RSS/API, GitHub GraphQL, web feeds), schema validation via Pydantic v2, data manipulation, vector embeddings, and LLM orchestration. 

We need a tooling stack that:
1. Enforces deterministic dependency resolution and rapid virtual environment creation.
2. Guarantees cross-environment parity between local developer environments (Linux, macOS, containers) and remote GitHub Actions CI runners.
3. Provides strict static type checking and lightning-fast linting and code formatting to maintain enterprise software engineering standards.

## Options Considered
1. **Python 3.12 managed via `uv` (Selected)**:
   - Extremely fast dependency resolver and virtual environment manager built in Rust.
   - Native support for standard `pyproject.toml` (PEP 517/518/621).
   - Python 3.12 offers optimal stability, compatibility with all major LLM SDKs, PyTorch/vector libraries, and substantial performance improvements over 3.11.
2. **Python Poetry**:
   - Mature ecosystem, but significantly slower dependency resolution and environment management compared to `uv`.
3. **Pip + Pip-tools**:
   - Minimalist, but lacks unified project lifecycle tooling, script execution, and modern lockfile ergonomics.

## Decision Rationale
We adopt **Python 3.12** as the target language runtime, managed via **`uv`**:
- `pyproject.toml` as the unified project configuration standard.
- `ruff` for ultra-fast linting and formatting (replacing flake8, black, isort).
- `mypy` with strict configuration for static type safety.
- `pytest` with `pytest-asyncio` for unit and integration testing.
- Lockfile tracking via `uv.lock` committed to source control to prevent dependency drift.

## Consequences
### Positive
- Near-instantaneous CI runs and local setup times.
- Strict typing and linting enforced prior to code merge.
- Native parity between local development and containerized/CI environments.

### Negative / Trade-offs
- Developers must have `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh` or distribution package).
- Strict typing (`mypy --strict`) requires comprehensive type hints across all modules.
