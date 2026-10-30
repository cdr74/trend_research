# Trend Horizon Radar: User Guide & Operator Manual

## ⚡ Quick Reference Cheatsheet (TL;DR)

If you only need the commands to get your work done, use these copy-pasteable recipes:

| Workflow Intent | Command Line | What It Does |
| :--- | :--- | :--- |
| **1. First-Time Setup** | `uv sync && uv run radar ui` | Prepares backend, installs frontend dependencies, verifies DB, and launches dashboard. |
| **2. Initial 1-Year Sync** | `uv run radar sync --days 365 --reset --ui` | Ingests 365-day baseline, evaluates, saves to DB, exports data bundle, and opens web UI. |
| **3. Launch Web Dashboard** | `uv run radar ui` (or `radar serve`) | Verifies prerequisites, starts Vite server, and opens `http://localhost:5173`. |
| **4. Routine Update (Delta)** | `uv run radar sync` | Ingests only *new* signals since your last sync, updates DB & web dashboard. |
| **5. Full Reset & Rebuild** | `uv run radar sync --days 365 --reset` | Clears all watermarks and recalculates the complete radar from scratch. |
| **6. Fast Offline Mock Run** | `uv run radar sync --mock --ui` | Zero-token smoke test using deterministic mock fixtures, opens dashboard immediately. |

---

### 📋 Common Task Recipes

#### Recipe 1: First-Time Use (Single Command to Running Radar)
```bash
# Sync dependencies, ingest 1-year historical baseline, and launch the web UI:
uv sync
uv run radar sync --days 365 --reset --ui
```

#### Recipe 2: Launching / Opening the Web Dashboard
```bash
# Checks database health, validates data bundle, and launches Vite on http://localhost:5173:
uv run radar ui
```

#### Recipe 3: Routine Update (Daily / Weekly Delta Ingestion)
```bash
# Delta sync: queries only newly published signals since the last run
uv run radar sync
```
*(The web dashboard updates automatically if already open in your browser).*

#### Recipe 4: Complete Reset (Wipe Watermarks & Re-baseline)
```bash
# Resets the state watermark file and runs a fresh 365-day historical re-evaluation
uv run radar sync --days 365 --reset
```

#### Recipe 5: Instant Mock Preview (No Waiting, No API Keys)
```bash
# Populates mock items and opens web dashboard immediately:
uv run radar export --mock
uv run radar ui
```

---

## 1. Introduction & Operating Philosophy

The **Trend Horizon Radar** is an autonomous intelligence platform designed for software engineering professionals and technology leaders. It continuously monitors, filters, corroborates, and evaluates emerging technology trends, enforcing deterministic anti-hype penalties, multi-source topic convergence, audience engagement velocity tracking, and multi-lens adversarial evaluation via domain profiles (default: Software Quality Engineering).

### 1.1 Local-First Architecture (WSL / Linux / macOS)
The platform is designed around a **local-first, on-demand execution model**:
- **No Cloud Cron Required:** You do not need to maintain complex serverless cron jobs or cloud runners. Whenever you are working at home or in your office using WSL or Linux, you trigger an incremental delta sync (`radar sync`).
- **Stateful Watermark Tracking:** The engine maintains watermark timestamps for every configured ingestion source in `data/.sync_state.json`. When you run a sync, it queries only for the time delta since your previous execution.
- **Hermetic & Offline-Capable:** All evaluations can run against cloud LLMs (Google Gemini, OpenAI-compatible APIs), air-gapped local models (Ollama/vLLM), or deterministic mock transports for zero-cost offline testing.

---

## 2. Prerequisites & First-Time Setup

### 2.1 System Requirements
- **Operating System:** Linux (Ubuntu/Debian, Fedora, Arch) or Windows Subsystem for Linux (WSL2 recommended). macOS is also supported.
- **Python Runtime:** Python 3.12+ managed via [`uv`](https://astral.sh/uv).
- **Container Engine:** Podman (recommended) or Docker for hosting the local PostgreSQL 16 + pgvector instance.
- **Node.js Environment:** Node.js 20+ and npm (for the interactive web dashboard).

### 2.2 Step-by-Step Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/cdr74/trend_research.git
   cd trend_research
   ```

2. **Sync Python Virtual Environment:**
   Install all dependencies, development tools, and package scripts into an isolated `.venv`:
   ```bash
   uv sync
   ```

3. **Configure Environment Variables:**
   Create your local `.env` file from the provided template:
   ```bash
   cp .env.example .env
   ```
   Inspect and customize `.env`:
   | Variable | Description | Default / Example |
   | :--- | :--- | :--- |
   | `RADAR_DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://radar:radar_secret@localhost:5432/radar_db` |
   | `RADAR_LLM_PROVIDER` | Active LLM adapter | `gemini` (options: `gemini`, `openai_compat`, `ollama`, `agy`, `mock`) |
   | `GEMINI_API_KEY` | API key if using Google Gemini | `your-gemini-api-key` |
   | `OLLAMA_BASE_URL` | Base URL if using local Ollama | `http://localhost:11434` |
   | `GITHUB_TOKEN` | Optional GitHub PAT (avoids public rate limits) | `ghp_...` |
   | `RADAR_INITIAL_LOOKBACK_DAYS` | Default lookback for first-time sync | `365` |
   | `RADAR_WATERMARK_BUFFER_DAYS` | Overlap safety buffer for delta queries | `2` |

4. **Local Database & Container Lifecycle:**
   Radar uses PostgreSQL 16 + pgvector declared in `compose.yaml`.
   - **Manual Start (optional):** `podman compose up -d` (or `docker compose up -d`).
   - **Interactive Auto-Start with Consent:** You do **not** need to manually start or stop the database every session! If you open a fresh WSL session after a reboot and run `radar sync`, Radar detects that PostgreSQL is offline and asks for your consent:
     ```text
     Notice: PostgreSQL database (radar-postgres) is not running on localhost:5432.
     Would you like to start it now via 'podman compose up -d'? [Y/n]:
     ```
     Pressing `Y` (the default) will automatically start the container in the background, wait ~1 second for health checks to pass, initialize schemas (`init_db()`), and proceed seamlessly.
   - **Stopping the Database:** You do **not** need to stop it after each session. It sits idle in the background consuming ~25 MB RAM and 0% CPU, and all data is preserved in the `pgdata` volume.

5. **Verify Installation with an Offline Smoke Test:**
   Execute a dry run using the mock provider:
   ```bash
   RADAR_LLM_PROVIDER=mock uv run radar sync --mock --limit-per-source 1
   ```
   If this completes with a green summary table, your local environment is fully configured!

---

## 3. Core Operator Flows

```mermaid
flowchart TD
    A["Operator runs 'radar sync'"] --> B{"Sync State exists in 'data/.sync_state.json'?"}
    B -->|"No (or --reset)"| C["Initial Baseline Lookback (365 days)"]
    B -->|"Yes"| D["Incremental Delta Query (since last_synced_at - 2 days)"]
    C --> E["Multi-Channel Ingestors (arXiv, GitHub, RSS)"]
    D --> E
    E --> F["Stage 1: Heuristic Noise Sieve (Drop Hype > 0.60)"]
    F --> G["Raw Payloads Stored in PostgreSQL"]
    G --> H["Stage 2: Deep Extractor (Embeddings & Claims)"]
    H --> I["Stage 3: Dynamic Bounded Topic Convergence (pgvector Cosine >= 0.65, <= 12 Themes)"]
    I --> J["Stage 4: Multi-Lens Adversarial Committee (Security, Ops, Rigor)"]
    J --> K["Radar Categorizer (Adopt, Trial, Assess, Hold)"]
    K --> L["Update Watermarks in 'data/.sync_state.json'"]
    L --> M["Present Summary Table to Operator"]
```

---

### Flow 1: Initial Baseline Ingestion (365-Day Historical Bootstrap)

#### Why 365 Days?
Emerging engineering paradigms and tools do not emerge in a vacuum; they build upon academic pre-prints, open-source prototypes, and engineering post-mortems published over the preceding year. Bootstrapping with a 365-day baseline gives the radar the necessary historical grounding to:
1. Accurately calculate audience engagement velocity ($\Delta \text{stars}/\Delta t$, citation growth).
2. Corroborate commercial marketing claims against earlier foundational research papers.
3. Detect repetitive wrappers repackaging existing academic algorithms.

#### Execution Command
```bash
# Full 365-day initial baseline across all active catalog sources (default: 20 records/source):
uv run radar sync --days 365

# Deeper baseline for high-volume streams (arXiv, GitHub, HackerNews):
uv run radar sync --days 365 --limit-per-source 50

# Or cap records per source for a faster initial trial:
uv run radar sync --days 365 --limit-per-source 10
```

#### What Happens Behind the Scenes:
1. Radar reads `data/seeds/sources.yaml` to discover all enabled channels.
2. Because `data/.sync_state.json` does not yet contain recorded watermarks, it sets the query window to `[now - 365 days, now]`.
3. The ingestors poll arXiv, GitHub, and RSS feeds for items published or updated within the last 365 days.
4. Stage 1 drops promotional listicles and blatant marketing buzzwords.
5. Qualified signals are written to the database.
6. Stages 2–4 extract facts, cluster topics in `pgvector`, convene the adversarial committee, and assign radar rings.
7. `data/.sync_state.json` is created with updated timestamps for each source.

---

### Flow 2: Routine On-Demand Incremental Delta Sync (WSL Workflow)

#### The Routine WSL Habit
Whenever you sit down at your workstation, simply execute:
```bash
uv run radar sync
```

#### How Delta Sync Operates:
- **Zero Configuration Needed:** You don't need to specify dates. Radar reads the exact timestamp when each source was last successfully polled from `data/.sync_state.json`.
- **2-Day Overlap Buffer:** Radar automatically rolls the watermark back by 2 days (`RADAR_WATERMARK_BUFFER_DAYS`) to guarantee that backdated arXiv pre-prints, delayed RSS syndications, or retroactive GitHub commit updates are never missed.
- **Deduplication:** Raw payloads are indexed by their unique source URI; duplicate signals are merged without redundant reprocessing.
- **Evaluation DAG:** Only newly ingested, un-evaluated signals are submitted to the 4-stage evaluation DAG.

#### Useful Flags:
```bash
# Limit or expand records ingested per source stream (default: 20)
uv run radar sync --limit-per-source 50

# Automatically start PostgreSQL container without interactive prompt if offline
uv run radar sync --auto-start-db

# Run strictly in offline mode without database persistence or container checks
uv run radar sync --no-db

# Run using offline mock LLM (ideal when checking pipeline mechanics without using API tokens)
uv run radar sync --mock
```

##### Command-Line Flags Reference (`radar sync`)
| Flag | Default | Description |
| :--- | :---: | :--- |
| **`--limit-per-source`** | `20` | Maximum candidate records fetched per source stream. Limits LLM token cost and prevents hitting GitHub unauthenticated rate limits. |
| **`--days`** | *N/A* | Override lookback window in days (e.g. `--days 365` for initial bootstrap). |
| **`--since`** | *N/A* | Explicit ISO-8601 timestamp cutoff (`YYYY-MM-DD`). |
| **`--reset`** | `false` | Clear all recorded watermarks and force re-ingestion across all active channels. |
| **`--reset-source`** | *N/A* | Reset watermark for a single specific source ID from `sources.yaml`. |
| **`--no-eval`** | `false` | Ingest raw sources into PostgreSQL but skip running LLM Stages 2–4. |
| **`--no-export`** | `false` | Ingest and evaluate without rewriting `web/public/radar.json`. |
| **`--ui`** | `false` | Launch local web dashboard automatically upon sync completion. |
| **`--mock`** | `false` | Run with offline deterministic mock payloads and mock evaluation responses. |
| **`--auto-start-db`** | `false` | Automatically launch `podman compose up -d` without prompting. |
| **`--no-db`** | `false` | Run without connecting to or writing to PostgreSQL. |

---

### Flow 3: Managing, Adding & Changing Sources (`data/seeds/sources.yaml`)

All intelligence feeds monitored by the radar are declaratively defined in [`data/seeds/sources.yaml`](file:///home/chris/dev/trend_research/data/seeds/sources.yaml).

#### Catalog File Schema
```yaml
sources:
  - id: "unique-source-slug"          # Immutable identifier used for state tracking
    name: "Human-Readable Name"       # Display name in reports and CLI
    channel: "rss"                    # Channel type: "academic" | "github" | "rss" | "community"
    endpoint_url: "https://..."       # Feed URL or API endpoint
    authority_weight: 1.25            # Credibility multiplier (1.0 = baseline, 1.3 = academic peer-reviewed)
    enabled: true                     # Active status (set to false to mute)
    query_params:                     # Channel-specific parameters
      keywords: ["testing", "agent"]  # For RSS: keyword filter
      # search_query: "cat:cs.SE"     # For arXiv: query string
      # q: "topic:llm-evals"          # For GitHub: search query
    telemetry_fields: ["views"]       # Telemetry signals to track
    description: "Scope and rationale for tracking this source."
```

#### Common Customization Tasks:

1. **Adding a New Engineering Blog (RSS / Atom):**
   Append the source to `data/seeds/sources.yaml`:
   ```yaml
   - id: "datadog-eng-blog"
     name: "Datadog Engineering Blog"
     channel: "rss"
     endpoint_url: "https://dtdg.co/eng-feed"
     authority_weight: 1.2
     enabled: true
     query_params:
       keywords: ["testing", "observability", "ai", "reliability"]
     description: "Production observability, synthetic monitoring, and reliability engineering."
   ```

2. **Adding a New GitHub Topic or Search Query:**
   ```yaml
   - id: "github-topic-agent-evals"
     name: "GitHub Topic: Agent Evals"
     channel: "github"
     endpoint_url: "https://api.github.com/search/repositories"
     authority_weight: 1.1
     enabled: true
     query_params:
       q: "topic:agent-evals OR topic:llm-benchmarks sort:updated"
     description: "Open source benchmarks and test harnesses for autonomous AI agents."
   ```

3. **Adding an arXiv Research Category:**
   ```yaml
   - id: "arxiv-cs-cr"
     name: "arXiv Cryptography and Security (cs.CR)"
     channel: "academic"
     endpoint_url: "http://export.arxiv.org/api/query"
     authority_weight: 1.3
     enabled: true
     query_params:
       search_query: "cat:cs.CR"
       max_results: 30
       sort_by: "submittedDate"
       sort_order: "descending"
     description: "Security analysis, adversarial attacks, and prompt injection mitigations."
   ```

4. **Temporarily Muting a Source:**
   Set `enabled: false`. On the next `radar sync`, the source will simply be skipped without losing its past watermark or stored signals.

---

### Flow 4: State Management & Watermark Resets

The synchronization watermark state is stored in `data/.sync_state.json`. You can easily reset all or part of the state at any time:

#### 1. Resetting a Single Source (`--reset-source`)
When you modify a source's URL or refine its search query in `data/seeds/sources.yaml`, you may want to re-ingest historical records for just that source without re-fetching all other channels:
```bash
# Reset only the Netflix Tech Blog watermark back 90 days:
uv run radar sync --reset-source netflix-tech-blog --days 90

# Reset only GitHub Test Generation back 365 days:
uv run radar sync --reset-source github-topic-test-generation --days 365
```

#### 2. Global Watermark Reset (`--reset`)
To clear all source watermarks and perform a fresh historical sync across every active source:
```bash
uv run radar sync --reset --days 365
```

#### 3. Manual State Inspection & Deletion
Because `data/.sync_state.json` is a plain JSON document:
```bash
# View current watermark timestamps and stats:
cat data/.sync_state.json

# Hard wipe the watermark file (forces full baseline sync on next run):
rm -f data/.sync_state.json
```

#### 4. Complete Database & State Wipe (Nuclear Reset)
To purge both the database and the watermark file and start 100% fresh:
```bash
podman compose down -v
podman compose up -d
rm -f data/.sync_state.json
uv run radar sync --days 365
```

---

### Flow 5: Ad-Hoc / Granular CLI Ingestion & Evaluation

If you prefer to run individual pipeline stages separately instead of using the unified `radar sync` command:

```bash
# Ingest from specific sources only, saving raw payloads to Postgres:
uv run radar ingest --sources arxiv,github --limit 20 --save

# Ingest with an ad-hoc query override:
uv run radar ingest --sources github --query "topic:property-testing sort:stars" --limit 10 --save

# Run evaluation DAG on un-evaluated signals stored in Postgres:
uv run radar evaluate --batch-size 25

# Run evaluation DAG in offline mock mode:
RADAR_LLM_PROVIDER=mock uv run radar evaluate
```

---

### Flow 6: Signal Discovery, Searching & CLI Audits

#### 1. Standard Field Filtering
```bash
# Show all tools placed in the Adopt ring:
uv run radar query --ring Adopt

# Filter by software quality engineering category:
uv run radar query --category "Test Synthesis"

# Limit output rows:
uv run radar query --ring Trial --limit 5
```

#### 2. Free-Format Token Syntax Searching
The CLI query engine includes an expressive token parser:
```bash
# Filter by ring and viability threshold:
uv run radar query "ring:Adopt viability:>0.80"

# Filter by evidence tier and low hype:
uv run radar query "tier:oss hype:<0.35"

# Combine multiple constraints:
uv run radar query "ring:Trial viability:>0.75 tier:academic"
```
**Supported Tokens:**
- `ring:Adopt` / `ring:Trial` / `ring:Assess` / `Hold`
- `viability:>0.80` / `viability:<0.60`
- `hype:<0.40` / `hype:>0.70`
- `tier:oss` / `tier:academic` / `tier:post_mortem` / `tier:vendor`
- `category:"<Name>"`

#### 3. Free-Text Keyword Search
Enter natural language terms to search across signal names, summaries, and key innovations:
```bash
uv run radar query "mutation testing bytecode"
uv run radar query "flaky test predictive runner"
```

#### 4. Direct Ad-Hoc SQL Queries
Execute direct `SELECT` statements against the underlying PostgreSQL tables:
```bash
uv run radar query --sql "SELECT name, ring, viability_score, hype_score, key_innovation FROM radar_items WHERE viability_score > 0.85 ORDER BY viability_score DESC"
```

#### 5. Deep Dossier Inspection (`radar inspect`)
Inspect the full adversarial committee audit, skeptic critique, and corroborating sources for any signal:
```bash
uv run radar inspect --id <SIGNAL_UUID>
```
Output includes:
- **Composite Scores:** Viability ($E_v$), Validity ($S_v$), Hype Score ($H$).
- **Committee Breakdown:** Security & Privacy (35%), Operational Feasibility (35%), Technical Rigor (30%).
- **Skeptic Critiques:** Identified architectural risks, runner bottlenecks, and failure modes.
- **Corroborating Evidence:** Linked arXiv pre-prints, GitHub repositories, and blog case studies.

---

### Flow 7: Generating Executive Markdown Intelligence Digests

The platform can compile automated Markdown digests summarizing portfolio movements and high-hype warnings:

```bash
# Generate executive digest for current calendar week:
uv run radar report --output reports/$(date +%Y-W%V).md

# Generate test report in offline mock mode (no live database required):
uv run radar report --output reports/test_digest.md --mock
```

#### Report Structure:
1. **Executive Portfolio Summary:** Aggregate distribution of signals across rings and categories.
2. **Ring Influx & Departures:** Newly promoted Adopt/Trial signals with their key innovations.
3. **Consensus & Multi-Source Convergence:** Clustered trends showing independent corroboration across academic research and open-source tooling.
4. **Adversarial Committee Warnings:** High-hype or risky tools placed into Hold with quotes from the Skeptic Committee.

---

### Flow 8: Decoupled Interactive Web Dashboard

The web dashboard is a modern Vite + React + TypeScript single-page application located in `web/`.

```mermaid
flowchart LR
    A["PostgreSQL Database"] -->|"uv run radar export"| B["web/public/radar.json\n(with 2D UMAP Projections)"]
    B --> C["Vite Dev Server\n(http://localhost:5173)"]
    C --> D["Quadrant Polar Radar (with Pan & Zoom)"]
    C --> E["Filterable Matrix Table"]
    C --> G["Semantic UMAP Clusters (with Pan & Zoom)"]
```

#### 1. Export Latest Database Bundle
Export the static dataset with 2D UMAP non-linear manifold projection coordinates:
```bash
uv run radar export --format json --output web/public/radar.json
```

#### 2. Start Local Development Server
```bash
cd web
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.

#### 3. Dashboard Features & Views:
- **Dual-Track Domain Switcher:** Sub-header tab bar allowing instant switching between **All Tracks**, **Software Testing (Deterministic)**, and **AI Evaluation (Non-Deterministic)** with live signal counts.
- **Radar Quadrant View:** Polar visualization across 4 concentric rings (Adopt, Trial, Assess, Hold) partitioned into 6 Software Quality Engineering pillars. Features **smooth mouse-wheel zoom, click-and-drag pan**, and floating HUD controls (`[+]`, `[-]`, `[Reset]`) to inspect dense clusters without label overlap.
- **Matrix Table View:** Comprehensive tabular data grid with column header click-sorting, inline dropdown filters, and dedicated **Track** and **Theme** badges. Click any row to expand the Committee Audit Drawer.
- **Semantic Cluster View:** 2D interactive spatial canvas projecting 1536-dimensional embeddings into 2D space using UMAP. Equipped with full **mouse-wheel zoom and drag-to-pan** to explore co-located entity clusters.
- **Search Omnibar:** Instant client-side search supporting structured tokens (`track:testing`, `track:evaluation`, `ring:Adopt`, `viability:>0.8`, `theme:<name>`, `risk:egress`) and plain keywords.

#### 4. Live Access on GitHub Pages (Zero Installation)
The dashboard is continuously deployed to GitHub Pages and available online at:
👉 **[https://cdr74.github.io/trend_research/](https://cdr74.github.io/trend_research/)**

Every push to `main` and every formal release triggers `.github/workflows/pages.yml`, publishing the latest evaluated data bundle and UI enhancements automatically.

#### 5. Offline GitHub Release Distribution Bundles
For air-gapped enterprise environments, internal wikis, or offline reviews, standalone static bundles are automatically built and attached to every [GitHub Release](https://github.com/cdr74/trend_research/releases):
- `radar-web-dashboard.zip` (Windows / universal)
- `radar-web-dashboard.tar.gz` (Linux / macOS)

**Running an Offline Bundle Locally:**
```bash
# 1. Unzip the release artifact
unzip radar-web-dashboard.zip
cd dist

# 2. Serve with any standard static file server (zero dependencies)
python3 -m http.server 8080
```
Then navigate to `http://localhost:8080` in any web browser.

#### 6. Building Static Production Bundle Locally
To compile the static bundle locally for custom hosting (Nginx, S3, Cloudflare Pages):
```bash
cd web
npm run build
```
The compiled output is emitted to `web/dist/` with relative asset links (`base: "./"`).

---

## 4. Understanding the Radar Scoring & Decision Model

### 4.1 Tech Radar Rings & Financial Decision Posture
Every evaluated signal is categorized into one of four rings reflecting executive urgency:

| Ring | Financial Enterprise Posture | Criteria & Viability Standard | Recommended Action |
| :--- | :--- | :--- | :--- |
| **Adopt** | **Established (MUST LOOK / DEPLOY)** | Viability $\ge 0.80$, Hype $\le 0.30$, strictly Consolidated lifecycle ($N \ge 3$ or stars $\ge 500$), zero compliance blockers | Immediate production implementation in target enterprise workflows. |
| **Trial** | **High-Confidence Pilot** | Viability $\ge 0.70$, Hype $\le 0.40$ (including high-viability emerging innovations) | Approved for sandboxed, non-critical internal banking applications or staging pipelines. |
| **Assess** | **Emerging (TEAM SHOULD TRACK)** | Viability $\ge 0.45$ or Velocity $\ge 25.0$; novel agent/eval proof | Track evolution for 6–18 month horizon; too early to experiment in-bank. |
| **Hold** | **Prohibited / High Risk** | Viability $< 0.45$, excessive hype ($> 0.60$), superficial wrapper, or prohibitive security risk | Avoid. Incompatible with financial regulations, superficial wrapper, or unverified claims. |

### 4.2 Dual-Track Taxonomy: Testing vs. Evaluation
The radar organizes signals across two distinct tracks:
1. **Software Testing (Deterministic Systems):** Verifying traditional software codebases (unit, integration, property-based invariants, mutation testing, predictive test selection, flaky test healing).
2. **AI Evaluation (Non-Deterministic Systems):** Assessing probabilistic models and agent systems (LLM benchmark harnesses, behavioral drift, hallucination detection, adversarial red-teaming, statistical confidence intervals).
3. **Cross-Cutting Agentic SDLC & Adequacy Evidence:** Providing calibrated confidence scores to the accountable human-in-the-loop and mathematical evidence of test adequacy (mutation scores, formal invariants) before machine-generated code is deployed.

### 4.3 Adversarial Multi-Lens Committee
Each candidate signal is evaluated across three weighted governance lenses:
1. **Security & Privacy Lens (35%):** Assesses egress boundaries, secret hygiene, code confidentiality, and local-model execution capabilities.
2. **Operational Feasibility Lens (35%):** Assesses execution determinism, CI runner footprint, maintenance overhead, and flake rates.
3. **Technical Rigor Lens (30%):** Evaluates empirical benchmarks vs synthetic marketing, formal contracts, and edge-case resilience.

Composite Viability Formula:
$$E_v = 0.35 \cdot S_{\text{sec}} + 0.35 \cdot S_{\text{ops}} + 0.30 \cdot S_{\text{tech}}$$

### 4.4 Multi-Source Consensus Bonus & Wrapper Penalty
- **Consensus Bonus (+0.25):** Awarded when independent sources from distinct channels (e.g. an arXiv paper, a GitHub repo, and an engineering blog) converge on the same algorithmic pattern.
- **Wrapper Penalty (-0.20):** Deterministically applied when a tool has semantic cosine similarity $\ge 0.88$ to an existing model or paper without offering distinct architectural novelties or unique datasets.

---

## 5. Development, CI/CD & Quality Gates

### 5.1 Local Verification Commands
Before submitting changes or creating pull requests, execute the automated test and lint suite:

```bash
# 1. Run all unit and integration tests hermetically (155 tests, ~18 seconds):
uv run pytest -v

# 2. Check code style and formatting:
uv run ruff check .
uv run ruff format --check .

# 3. Enforce strict static type checking:
uv run mypy src tests
```

### 5.2 Automated Release Automation (Google Release Please)
The repository enforces Semantic Versioning (SemVer) driven by Conventional Commits:
- Pushes to `main` with `feat:` or `fix:` commits trigger the Release Please GitHub Actions workflow.
- Release Please automatically creates and maintains a Release PR updating `CHANGELOG.md` and version numbers.
- Merging the Release PR triggers the publishing workflow:
  - Cuts a Git release tag (e.g., `v0.5.0`).
  - Builds Python distributions (`.whl` and `.tar.gz`) via `uv build`.
  - Packages the static web dashboard (`radar-web-dashboard.tar.gz`).
  - Publishes the GitHub Release with attached assets.

### 5.3 GitHub Branch Protection & Safety Guardrails
The default branch (`main`) is governed by an active GitHub Repository Ruleset (**Guardrail Protection for Main**):
- **Non-Fast-Forward Protection (Block Force Pushes):** Prohibits `git push --force origin main`, preventing accidental history overwrites or commit loss.
- **Deletion Protection:** Prohibits deletion of the default branch (`git push origin :main`).
- **Direct Push Velocity:** Fast-forward pushes by repository maintainers remain fully supported following local verification (`pytest`, `mypy`, `ruff`), preserving seamless pair-programming iteration while maintaining structural safety. Release Please PR automation merges cleanly without artificial review blockades.

---

## 6. Troubleshooting & Operator FAQ

### 1. `asyncpg.exceptions.CannotConnectNowError: connection refused`
- **Cause:** PostgreSQL container is not running.
- **Fix:** Run `podman compose up -d` (or `docker compose up -d`) and wait 5 seconds before retrying.

### 2. `github.RateLimitExceededException` during ingestion
- **Cause:** Unauthenticated GitHub API calls are limited to 60 requests/hour per IP.
- **Fix:** Generate a personal access token on GitHub and add it to `.env`:
  ```bash
  GITHUB_TOKEN=ghp_your_token_here
  ```

### 3. `radar sync` fetched 0 new records
- **Cause:** Your sources are already up to date according to `data/.sync_state.json`.
- **Fix:** If you want to force re-ingestion, use `--reset` or `--days 365`:
  ```bash
  uv run radar sync --reset --days 365
  ```

### 4. LLM API Key errors or quota limits
- **Cause:** `GEMINI_API_KEY` is missing or has exceeded rate limits.
- **Fix:** Switch temporarily to the offline mock provider (`RADAR_LLM_PROVIDER=mock`) or use a local Ollama model (`RADAR_LLM_PROVIDER=ollama`).

### 5. Web dashboard shows empty radar or stale data
- **Cause:** `web/public/radar.json` has not been refreshed since the latest evaluation.
- **Fix:** Re-export the data bundle from the root directory:
  ```bash
  uv run radar export --format json --output web/public/radar.json
  ```

### 6. Why do high-volume feeds (arXiv, GitHub, HackerNews) only ingest 20 records?
- **Cause:** By default, `radar sync` enforces a batch cap of `--limit-per-source 20` across each enabled channel.
- **Why is there a default cap?**
  1. **LLM Cost & Token Budget:** Every signal that passes the Stage 1 Heuristic Sieve is sent through Stage 2 (Deep Extraction) and Stage 3 (Adversarial Evaluator Committee). Ingesting hundreds of items in a single run would trigger hundreds of multi-lens LLM API calls and consume significant token budgets.
  2. **API Rate-Limit Protection:** Unauthenticated GitHub search is strictly capped at 10 requests per minute. Limiting to 20 records per topic ensures all 6 GitHub streams complete within quota without hitting HTTP 403 errors.
  3. **Incremental Delta Velocity:** The radar is designed for routine WSL / desktop operation. Once an initial baseline is established, routine delta runs rarely encounter more than 5–15 new articles per channel.
- **Fix:** To ingest a deeper historical batch, pass `--limit-per-source <N>`:
  ```bash
  # Ingest up to 50 records per source stream
  uv run radar sync --days 365 --limit-per-source 50

  # Ingest up to 100 records per source stream without running LLM evals immediately:
  uv run radar sync --days 365 --limit-per-source 100 --no-eval
  ```
