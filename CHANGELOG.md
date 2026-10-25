# Changelog

All notable changes to the Trend Horizon Radar platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-25

### Features
- **Core Models & Persistence**: Implemented Pydantic v2 domain schemas, PostgreSQL 16 + pgvector persistence layer via SQLAlchemy 2.0 async.
- **Multi-Source Ingestion**: Asynchronous multi-channel ingestion collectors for arXiv (Atom API), GitHub Repositories (REST API), and practitioner RSS feeds with rate-limiting and telemetry normalization.
- **Noise Filtering & Extraction**: Stage 1 deterministic Heuristic Noise Sieve and Stage 2 Deep Extractor Agent with vector embeddings.
- **Convergence & Wrapper Detection**: pgvector semantic topic clustering, cross-source corroboration consensus bonus (+0.25), and parasitic wrapper penalties (-0.20).
- **Multi-Lens Committee Evaluation**: Stage 3 multi-lens committee evaluator (Security & Privacy, Operational Feasibility, Technical Rigor).
- **Radar Categorization & Golden Benchmark**: Stage 4 Radar Categorizer with deterministic viability ($E_v$), validity ($S_v$), and hype penalty ($H$). 20-item Golden Benchmark suite passing with 100% recall.
- **Executive Reporting & CLI**: Command-line tool (`radar ingest`, `radar evaluate`, `radar query`, `radar inspect`, `radar report`, `radar export`) with Markdown digest generation and offline safety guards.
- **2D Projection & Web Dashboard**: Non-linear UMAP 2D manifold projection, 4-view interactive web dashboard (Radar Quadrant, Matrix Table, Scatter Matrix, Semantic Cluster Map), and search Omnibar with token parsing.
