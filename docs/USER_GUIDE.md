# Trend Horizon Radar: User Guide & Operator Manual

## 1. Introduction

The **Trend Horizon Radar** is an autonomous intelligence platform for professionals that continuously monitors, filters, corroborates, and evaluates emerging technology trends in times of rapid disruption.

This manual outlines how to operate the radar pipeline, run local evaluations, explore findings through interactive filters, track multi-source topic convergence, and interpret the scoring rubric.

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
   - `RADAR_LLM_PROVIDER`: `gemini` (or `openai_compat`, `ollama`, `agy`, `mock`)
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
Fetch fresh records, calculate live engagement velocity, and evaluate Stage 1 Noise Sieve verdicts:
```bash
# Ingest across all active channels (arXiv, GitHub, RSS)
uv run radar ingest --sources arxiv,github,rss --limit 5

# Query specific channels with custom topic or feed overrides
uv run radar ingest --sources arxiv --query "cat:cs.SE" --limit 5
uv run radar ingest --sources github --query "topic:test-generation sort:updated" --limit 5
uv run radar ingest --sources rss --query "https://netflixtechblog.com/feed" --limit 5

# Ingest and persist raw payloads to PostgreSQL
uv run radar ingest --sources arxiv,github,rss --limit 10 --save
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

# Filter by viability threshold and velocity
uv run radar query --min-viability 0.80 --max-hype 0.30

# Show full multi-lens committee audit and corroborating sources
uv run radar inspect --id <SIGNAL_UUID>
```

### 3.4 Export Data and Generate Reports
Export the static dataset and generate executive trend briefings:
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
- **Adopt:** Proven technical validity ($S_v \ge 0.80$), strong viability ($E_v \ge 0.85$), verified operational ergonomics, and high cross-source corroboration. Recommended for production pilot.
- **Trial:** High viability ($E_v \ge 0.70$) and promising innovation ($S_v \ge 0.60$). Worthy of sandboxed project trials to evaluate team workflows.
- **Assess:** High research merit or technical novelty, but early in enterprise maturity or requiring integration mitigations. Keep under active monitoring.
- **Hold:** Excessive marketing hype, superficial wrapper architecture, non-deterministic execution, or prohibitive privacy/security risks. Not recommended.

### 4.2 Multi-Source Corroboration & Velocity Dynamics
- **Corroboration Factor:** When independent sources (academic pre-prints, open-source repositories, practitioner engineering blogs) converge on the same pattern, the signal receives a positive consensus boost.
- **Audience Velocity:** Tracks time-decayed metric changes (stars, views, citations) to classify trends into **Emerging**, **Consolidated**, or **Fading**.

### 4.3 The 3 Multi-Lens Committee Evaluators
1. **Security & Privacy Lens (35%):** Egress boundaries, zero-trust / on-premise execution, credential safety.
2. **Operational Feasibility Lens (35%):** Deterministic reproducibility, runner compute footprint, integration ergonomics.
3. **Technical Rigor Lens (30%):** True defect/problem resolution vs synthetic benchmarks, contract adherence.

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
   - **Radar Quadrant:** Traditional interactive radar with 4 rings segmented across domain pillars.
   - **Filterable Matrix Table:** Tabular view with instant keyword search, column sorting, and deep dossier inspection.
   - **Topic Convergence View:** Inspect clusters of interconnected signals and corroborating sources.
   - **Scatter Matrix:** Interactive 2-axis scatter chart plotting Signal Validity vs. Viability.

3. **Filter Controls:**
   - Ring toggles (Adopt / Trial / Assess / Hold).
   - Pillar toggles.
   - Evidence Tier selector (Academic Peer-Reviewed, Open Source, Post-Mortem, Vendor).
   - Score sliders (Hype ceiling, Viability floor).
   - Lifecycle trajectory filter (Emerging / Consolidated / Fading).
