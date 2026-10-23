# ADR 0004: Pipeline DAG and Schema Contracts

## Status
Accepted

## Context
The radar operates as a 4-stage Directed Acyclic Graph (DAG):
1. **Source Ingestion:** Ingest raw feeds from academic repositories (arXiv SE), GitHub Trending / commit metrics, RSS, and curated engineering post-mortems.
2. **Stage 1 (Noise Sieve):** Heuristic and pattern filtering dropping vanity claims and low-density marketing (hype score > 0.60 drops early).
3. **Stage 2 (Deep Extractor):** Extract technical claims, evidence tier, reproducible datasets, and architectural taxonomy into a structured dossier.
4. **Stage 3 (Enterprise Skeptic):** Apply adversarial banking architect review against deployment topology, deterministic CI/CD reproducibility, data privacy, and auditability.
5. **Stage 4 (Radar Categorizer):** Compute composite scores (`hype_score`, `viability_score`) and assign Tech Radar ring (`Adopt`, `Trial`, `Assess`, `Hold`).

Inter-stage communication must be strictly validated to prevent schema drift, pipeline failures, or un-auditable outputs.

## Options Considered
1. **Pydantic v2 Models with Strict JSON Schema Export (Selected)**:
   - High performance validation via Pydantic core (Rust).
   - Python-native data structures with automatic serialization/deserialization to JSON and JSONB.
   - Dual-use: acts as Python type definitions and generates static standard JSON schemas (`signal.schema.json`, `dossier.schema.json`).
2. **Raw Dictionaries / TypedDicts**:
   - Lack runtime schema validation and parsing guarantees.
3. **Protobuf / gRPC**:
   - Overkill for batch/asynchronous pipeline processing with JSONB database storage.

## Decision Rationale
We adopt **Pydantic v2** as the single source of truth for pipeline contracts:
- Schemas strictly model the taxonomy: 6 QE categories (`Spec & Model`, `Test Synthesis`, `Execution & Optimization`, `Triage & Self-Healing`, `Agent Systems`, `Governance & Evals`).
- Explicit scoring rubrics modeled with mathematical bounds `[0.0, 1.0]`.
- Every stage produces an immutable Pydantic record persisted to PostgreSQL with audit timestamps and pipeline run IDs.

## Consequences
### Positive
- Strict runtime safety and type safety.
- Clear contract boundaries for testing each stage in isolation.
- Automatic schema documentation generation.

### Negative / Trade-offs
- Schema modifications require versioned database migrations (Alembic).
