# AI Test Engineering Horizon Radar: User Guide & Operator Manual

## 1. Introduction

The **AI Test Engineering Horizon Radar** provides engineering leadership, enterprise architects, and quality directors with deterministic, hype-filtered intelligence on AI-driven software testing innovations.

This manual outlines how to operate the radar pipeline, run local evaluations, explore findings through interactive filters, and interpret the scoring rubric.

---

## 2. Prerequisites & Quickstart

### 2.1 System Requirements
- Linux (x86_64 or aarch64) or macOS.
- Python 3.12+ and `uv` package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
- Podman (or Docker) for running the local PostgreSQL + pgvector database.
- Node.js 20+ (for building or serving the interactive web dashboard).

### 2.2 Environment Setup
1. Clone the repository and configure dependencies:
   ```bash
   git clone https://github.com/cdr74/trend_research.git
   cd trend_research
   uv sync
   ```

2. Configure environment variables in `.env` (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```
   Key variables:
   - `RADAR_DATABASE_URL`: `postgresql+asyncpg://radar:radar_secret@localhost:5432/radar_db`
   - `RADAR_LLM_PROVIDER`: `gemini` (or `openai_compat`, `ollama`, `mock`)
   - `GEMINI_API_KEY`: Your Gemini API key (if using Google Gemini provider)
   - `OLLAMA_BASE_URL`: `http://localhost:11434` (if running air-gapped local models)

3. Start the local database:
   ```bash
   podman compose up -d
   ```

---

## 3. Command Line Interface (CLI) Workflows

The `radar` CLI coordinates all pipeline actions:

### 3.1 Synchronize and Ingest Signals
Fetch fresh records from configured feeds (arXiv SE, GitHub Trending, RSS):
```bash
uv run radar ingest --sources arxiv,github,rss
```

### 3.2 Run Evaluation Pipeline
Execute the 4-stage evaluation DAG against newly ingested or un-evaluated records:
```bash
# Run with configured LLM provider
uv run radar evaluate --batch-size 20

# Run in offline mock mode (no API keys required, ideal for local smoke tests)
RADAR_LLM_PROVIDER=mock uv run radar evaluate
```

### 3.3 Query and Filter Signals
Query the local evaluated database from the terminal:
```bash
# Filter by ring and category
uv run radar query --ring Adopt --category "Test Synthesis"

# Filter by enterprise viability threshold
uv run radar query --min-viability 0.80 --max-hype 0.30

# Show full adversarial skeptic critique for a signal
uv run radar inspect --id <SIGNAL_UUID>
```

### 3.4 Export Data and Generate Reports
Export the static dataset and generate bi-weekly executive briefings:
```bash
# Export static JSON for web dashboard
uv run radar export --format json --output web/public/radar.json

# Generate bi-weekly Markdown intelligence digest
uv run radar digest --output reports/$(date +%Y-W%V).md
```

---

## 4. Understanding the Radar & Scoring Rubric

### 4.1 Tech Radar Rings
Every evaluated signal is placed into one of four rings:
- **Adopt:** Production-ready for enterprise pilots. Demonstrates high technical validity ($S_v \ge 0.80$), strong enterprise viability ($E_v \ge 0.85$), zero-egress compatibility, and deterministic behavior.
- **Trial:** High viability ($E_v \ge 0.70$) and promising innovation ($S_v \ge 0.60$). Worthy of sandboxed project trials to evaluate developer ergonomics.
- **Assess:** High research merit or technical novelty, but lacks proven enterprise hardening or requires cloud data-egress mitigations. Keep under active monitoring.
- **Hold:** Excessive marketing hype, superficial LLM wrapper architecture, non-deterministic execution, or prohibitive data privacy risks. Not recommended.

### 4.2 The 4 Banking Enterprise Viability Gates
1. **Deployment Topology:** Is the tool deployable within a zero-egress VPC or air-gapped on-premise container?
2. **Deterministic Reproducibility:** Does execution produce deterministic, replayable results, or does it introduce flaky non-determinism into CI/CD gates?
3. **Data Security & Privacy:** Does operation require transmitting proprietary code, database schemas, or production payloads to third-party endpoints?
4. **Auditability & Traceability:** Does the tool generate machine- and human-auditable reasoning traces suitable for regulatory compliance review?

---

## 5. Interactive Web Dashboard

The web dashboard (`web/`) offers dynamic multi-view exploration:

1. **Starting the Web Dashboard Locally:**
   ```bash
   cd web
   npm install
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

2. **Available Views:**
   - **Radar Quadrant:** Traditional interactive radar with 4 rings segmented across the 6 QE pillars.
   - **Filterable Matrix Table:** Tabular view with instant keyword search, column sorting, and deep dossier inspection.
   - **Scatter Matrix:** Interactive 2-axis scatter chart plotting Signal Validity vs. Enterprise Viability.
   - **Semantic Cluster Map:** Visual representation of embedding similarity clusters to spot redundant wrapper tools.

3. **Filter Controls:**
   - Ring toggles (Adopt / Trial / Assess / Hold).
   - Pillar toggles (Spec & Model, Test Synth, Execution & Optimization, Triage & Fix, Agent Systems, Governance & Evals).
   - Evidence Tier selector (Academic Peer-Reviewed, Open Source, Post-Mortem, Vendor).
   - Score sliders (Hype ceiling, Enterprise Viability floor).
   - Risk tag filters (e.g., "Requires Cloud Egress", "Non-Deterministic").
