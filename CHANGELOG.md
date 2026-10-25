# Changelog

All notable changes to the Trend Horizon Radar platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0](https://github.com/cdr74/trend_research/compare/v0.1.0...v0.2.0) (2026-10-25)


### Features

* **architecture:** generalize trend platform, add topic convergence and engagement velocity (Ref: ADR-0000, Backlog M1) ([c73c524](https://github.com/cdr74/trend_research/commit/c73c5247833a8b7e2e764c780754a4dc9717b089))
* **convergence:** implement pgvector topic convergence and wrapper detection (Ref: ADR-0012, Backlog M3-T3) ([7251598](https://github.com/cdr74/trend_research/commit/7251598837d9d5be21a4cb84e8e5b2949d6d062e))
* **evaluator:** implement Stage 3 Multi-Lens Committee Evaluator (Ref: ADR-0013, Backlog M3-T4) ([f659b0f](https://github.com/cdr74/trend_research/commit/f659b0f2378a4598f1eac59afe39fe7084b7770e))
* **ingestion:** establish curated multi-channel source catalog and registry loader (Ref: ADR-0000, Backlog M2-T1) ([66e0688](https://github.com/cdr74/trend_research/commit/66e06884d47963d6485cbebeab6692565620fb1c))
* **ingestion:** implement arXiv pre-print collector and CLI ingestion (Ref: ADR-0006, Backlog M2-T2) ([658891b](https://github.com/cdr74/trend_research/commit/658891bc3b40ec7671006d7a43bc8772ee6defdf))
* **ingestion:** implement BaseIngestor protocol and telemetry normalizer (Ref: ADR-0000, Backlog M2-T1) ([1809751](https://github.com/cdr74/trend_research/commit/1809751561612957c94f43558871612145f38510))
* **ingestion:** implement GitHub repository and RSS/Atom publication collectors (Ref: ADR-0007, ADR-0008, Backlog M2-T3, Backlog M2-T4) ([e782e2c](https://github.com/cdr74/trend_research/commit/e782e2c2afbc2aab037b2cd3f037f4022777fed2))
* **pipeline:** implement Stage 1 deterministic heuristic noise sieve (Ref: ADR-0009, Backlog M2-T5) ([9b47d69](https://github.com/cdr74/trend_research/commit/9b47d696a9cf25ef9692d5162a83eaec1b4b9397))
* **pipeline:** implement Stage 2 Deep Extractor agent with vector embeddings (Ref: ADR-0011, Backlog M3-T2) ([b9e9af1](https://github.com/cdr74/trend_research/commit/b9e9af11bfd4af3214b31754fc565c9e4054c329))
* **pipeline:** implement Stage 4 Golden Benchmark evaluation test suite (Ref: ADR-0015, Backlog M3-T6) ([446d04e](https://github.com/cdr74/trend_research/commit/446d04e4afd63d66f289e82153eeb3aa7fcd1954))
* **pipeline:** implement Stage 4 Radar Categorizer and Lifecycle Trajectory (Ref: ADR-0014, Backlog M3-T5) ([ccd94ee](https://github.com/cdr74/trend_research/commit/ccd94ee463f58c51dbd84acf7c60eb3b641858ef))
* **presentation:** implement CLI inspect and Markdown executive report generator (Ref: ADR-0016, Backlog M4-T1, M4-T2) ([66385c4](https://github.com/cdr74/trend_research/commit/66385c4fa1949f0bfdc98f8910744b8fe2d78a10))
* **presentation:** implement UMAP 2D projection, smart omnibar query, and multi-view web dashboard (Ref: ADR-0017, Backlog M4-T3, M4-T4, M4-T5) ([7d6bbf1](https://github.com/cdr74/trend_research/commit/7d6bbf1b9e343d12005f3fab7bc3d3ccf71de82a))
* **providers:** implement pluggable LLM adapters and local agy CLI bridge (Ref: ADR-0010, Backlog M3-T1) ([7e51d31](https://github.com/cdr74/trend_research/commit/7e51d319992a2f631636506383ec8fae674e042b))
* **release:** implement automated SemVer tagging and changelog via Release Please (Ref: ADR-0018, Backlog M5-T1) ([49d1f07](https://github.com/cdr74/trend_research/commit/49d1f07fca0a17abbf46df19d0b9ec931912fc5b))
* **scaffold:** initialize core skeleton, persistence, test harness, and web dashboard (Ref: ADR-0001..0005, Backlog M1-T2..T5) ([b335905](https://github.com/cdr74/trend_research/commit/b3359059401b66bde589c8fece1c2c0a573757fc))


### Bug Fixes

* **release:** assert boolean string comparison on releases_created (Ref: ADR-0018, Backlog M5-T1) ([5ee8464](https://github.com/cdr74/trend_research/commit/5ee84649f4d43086d4cd949586e870744a3f4184))
* **tests:** hermetically mock agy binary resolution for host-agnostic CI runners (Ref: ADR-0010) ([b60466b](https://github.com/cdr74/trend_research/commit/b60466b78af402fa5c3d9cbc232c149525690d9e))


### Documentation

* **adr:** add foundational ADR-0000 for overall system architecture (Ref: ADR-0000) ([a17decb](https://github.com/cdr74/trend_research/commit/a17decb8af0d78b4f65a0857dafacf20c0cbd68d))
* **adr:** lock in 1C, 2C, 3B architecture decisions in ADR-0000, schemas, and design docs (Ref: ADR-0000, Backlog M1-T1) ([03d6ede](https://github.com/cdr74/trend_research/commit/03d6edeb202cedac30f7d49b61d2059a2bca5e91))
* **backlog:** mark Milestone 1 complete and set Milestone 2 as next up (Ref: Backlog M2) ([61005f4](https://github.com/cdr74/trend_research/commit/61005f4f51ac099981051b2e283f44b3d294954e))
* **inception:** establish documentation architecture and engineering baseline (Ref: ADR-0001..0005, Backlog M1-T1) ([efff174](https://github.com/cdr74/trend_research/commit/efff17490ef16cd2a5102dc07bdae7f7dbd1bd48))
* synchronize milestone status and provider configuration in documentation ([8910617](https://github.com/cdr74/trend_research/commit/891061774265bd1f075386601269e5081f08e5f0))
* synchronize README index, roadmap milestones, and CLI user guide ([3f83b07](https://github.com/cdr74/trend_research/commit/3f83b074883faf8b9d81c1268c9be7ea8f36ea39))

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
