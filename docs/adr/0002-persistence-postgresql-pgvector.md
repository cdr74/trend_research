# ADR 0002: Persistence Layer with PostgreSQL and pgvector via Podman

## Status
Accepted

## Context
The Radar processes signals from raw ingestion through adversarial multi-agent evaluation to structured Radar categorizations. Beyond standard relational query patterns (filtering by category, evidence tier, ring, and hype/viability score bands), the system requires:
1. Deterministic storage of raw source payloads, intermediary extraction dossiers, and evaluation audit trails.
2. Semantic similarity clustering and deduplication (detecting "wrapper" tools that mirror existing models or tools with identical claims).
3. Flexible JSON schema persistence for evolving evaluation metrics while retaining strict relational integrity for core radar entities.
4. Clean containerized operation on developer workstations without root daemon dependencies.

## Options Considered
1. **Local PostgreSQL 16 + pgvector via Podman (Selected)**:
   - Industry-standard relational enterprise database with first-class JSONB support.
   - Native vector storage and indexing (HNSW / IVFFlat via `pgvector`) enables semantic search, duplicate detection, and automated clustering directly in SQL without an auxiliary vector database service.
   - Rootless, daemonless container management via Podman aligning with strict enterprise security policies.
   - Fully reproducible via `compose.yaml` / `podman compose`.
2. **SQLite + DuckDB**:
   - Zero-dependency embedded files, but lacks native concurrent vector extensions, robust JSONB indexing, and standard enterprise database parity.
3. **Dedicated Vector DB (e.g., Qdrant, Milvus, Chroma) alongside Relational DB**:
   - Introduces multi-store distributed transactions and architectural complexity for a bounded-scale evaluation corpus.

## Decision Rationale
We adopt **PostgreSQL 16 with `pgvector`**, managed locally via **Podman**:
- A single unified storage engine accommodates relational metadata, structured evaluation dossiers (JSONB), and semantic vector embeddings (vector dimensions matching selected embedding model, e.g. 1536 / 768).
- Podman provides rootless container execution adhering to enterprise workstation security baselines.
- Python database interaction is handled through **SQLAlchemy 2.0 (asyncio)** and **pgvector-python** / **asyncpg** with **Alembic** migrations.

## Consequences
### Positive
- Unified query engine for scalar filters (e.g. `ring = 'Adopt' AND viability_score >= 0.8`) and semantic similarity (e.g. `ORDER BY embedding <=> :target_vector LIMIT 5`).
- No vendor lock-in; standard PostgreSQL instance runs anywhere (local Podman, AWS RDS, GCP Cloud SQL, or on-prem Kubernetes).
- Full auditability and ACID transactional consistency for multi-stage pipelines.

### Negative / Trade-offs
- Requires Podman runtime installed on the local developer environment.
- CI pipeline in GitHub Actions must launch a PostgreSQL + pgvector service container for integration tests.
