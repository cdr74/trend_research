# Changelog

All notable changes to the Trend Horizon Radar platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0](https://github.com/cdr74/trend_research/compare/v0.8.0...v0.9.0) (2026-10-30)


### Features

* **ui:** streamline to 3-view layout and add svg pan-and-zoom (Ref: ADR-0027, Backlog M12) ([e62b415](https://github.com/cdr74/trend_research/commit/e62b4150fdfaabbdbcbe8d24b9cd8ec888262713))

## [0.8.0](https://github.com/cdr74/trend_research/compare/v0.7.0...v0.8.0) (2026-10-30)


### Features

* **ingestion:** stabilize feed endpoints, github pagination and hn community collector (Ref: ADR-0026, Backlog M11) ([b36d685](https://github.com/cdr74/trend_research/commit/b36d685dcdc1d1b312312be72a2eac5ff99da253))


### Documentation

* **architecture:** remove redundant intent spec and update doc index (Ref: ADR-0021, Backlog M10-T5) ([5c81cfd](https://github.com/cdr74/trend_research/commit/5c81cfdc33e6566423e803fc05e355b452ed3a49))
* **guide:** document limit-per-source parameter and tuning (Ref: ADR-0026, Backlog M11-T6) ([3b69bf0](https://github.com/cdr74/trend_research/commit/3b69bf0b7d91430ad70dd5dcfd1ca4cfeb3c3534))

## [0.7.0](https://github.com/cdr74/trend_research/compare/v0.6.0...v0.7.0) (2026-10-29)


### Features

* **domain:** implement dynamic bounded topic convergence and theme attribution (Ref: ADR-0023, Backlog M8) ([938f3d8](https://github.com/cdr74/trend_research/commit/938f3d8851f6cf3d0c783711281a9f8d2e943c9f))
* **ui:** implement table sorting, deterministic blip layout, and spec-model coverage (Ref: ADR-0024, Backlog M9) ([9f20850](https://github.com/cdr74/trend_research/commit/9f208504c7e44b98feca8fc0ef1b61b5194e3768))


### Bug Fixes

* **domain:** inherit consensus topic category in radar categorizer (Ref: ADR-0023, Backlog M8) ([381aec2](https://github.com/cdr74/trend_research/commit/381aec28e65ea5b8e337694f0e900c3dc975ce9a))

## [0.6.0](https://github.com/cdr74/trend_research/compare/v0.5.1...v0.6.0) (2026-10-29)


### Features

* **domain:** implement multi-gated radar ranking and lifecycle gates (Ref: ADR-0022, Backlog M7) ([39d44dc](https://github.com/cdr74/trend_research/commit/39d44dc45003f316dcbd37a6e5a202f52dc639f4))

## [0.5.1](https://github.com/cdr74/trend_research/compare/v0.5.0...v0.5.1) (2026-10-27)


### Documentation

* **github:** document Option A branch protection ruleset in user guide ([3586e2c](https://github.com/cdr74/trend_research/commit/3586e2c3169843a3936c0fb314b9df11f14bd613))

## [0.5.0](https://github.com/cdr74/trend_research/compare/v0.4.0...v0.5.0) (2026-10-27)


### Features

* **domain:** implement multi-tiered relevance filter and financial dual-track architecture (Ref: ADR-0021, Backlog M6) ([8495bb4](https://github.com/cdr74/trend_research/commit/8495bb42b60a13ba4f97424a76f86e5a51c2f4e1))
* **presentation:** add radar ui command, database upserts, and fix radar blip hover jitter (Ref: Backlog M5-T4) ([e56ec11](https://github.com/cdr74/trend_research/commit/e56ec11472c9e5d0d19b9efa9efccc7d1e3e98fb))


### Bug Fixes

* **ui:** synchronize live database signals and implement dual-track switcher (Ref: Backlog M6-T5) ([09896f4](https://github.com/cdr74/trend_research/commit/09896f4d4f9af99f4b451e4b443917780915d6ca))


### Documentation

* **math:** fix KaTeX and math mode rendering errors across markdown files ([aa026a6](https://github.com/cdr74/trend_research/commit/aa026a632078d5eb27a3c77837f96a1cbd82b591))
* **privacy:** sanitize documentation to remove role and personal references ([f4927cd](https://github.com/cdr74/trend_research/commit/f4927cd8503cd6ff2d76c7f4e22dd9d23a9ee5cd))
* **readme:** rewrite README to explicitly articulate intent, dual-track architecture, and doc index (Ref: ADR-0021, Backlog M6) ([e9666d2](https://github.com/cdr74/trend_research/commit/e9666d25cdc5f27d2fc178df57e8d71b850d4cef))
* update README and USER_GUIDE for dual-track architecture and UI switcher (Ref: ADR-0021, Backlog M6) ([797cf19](https://github.com/cdr74/trend_research/commit/797cf19167fcf04f38c26b7209fc7ea98f8857b6))

## [0.4.0](https://github.com/cdr74/trend_research/compare/v0.3.0...v0.4.0) (2026-10-25)


### Features

* **cli:** prompt for user consent to start database container when offline (Ref: ADR-0020, Backlog M5-T3) ([96b5b45](https://github.com/cdr74/trend_research/commit/96b5b45b28acf58740e497fa480f5d44f89a58c9))


### Bug Fixes

* **docs:** resolve Mermaid syntax error in USER_GUIDE.md ([847f26e](https://github.com/cdr74/trend_research/commit/847f26e78be6ff5c61f90ff8854dbbfd29aa8760))

## [0.3.0](https://github.com/cdr74/trend_research/compare/v0.2.0...v0.3.0) (2026-10-25)


### Features

* **pipeline:** implement on-demand incremental sync and watermark tracking (Ref: ADR-0019, Backlog M5-T2) ([722ce71](https://github.com/cdr74/trend_research/commit/722ce71f13ee6e276507e2f8b262c5c6edaea748))

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
