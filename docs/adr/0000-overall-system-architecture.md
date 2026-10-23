# ADR 0000: Macro System Architecture & End-to-End Processing Topology

## Status
Accepted (Deliberated and locked with Engineering)

---

## 1. Context & Problem Statement

### 1.1 Enterprise Background & The Hype Inundation
In the wake of rapid proliferation of generative AI and agentic software development life cycle (SDLC) tooling, engineering leadership—particularly in high-governance, regulated financial institutions (e.g., Tier-1 investment banks, wealth management, payment networks)—is inundated with:
- Aggressive vendor marketing and PR announcements.
- Ephemeral wrappers around commodity proprietary models with minimal domain engineering.
- Unverified, synthetic, or non-reproducible academic and corporate benchmarks (e.g., "99% automated bug fixing" measured on trivial synthetic codebases).
- Affiliate-driven influencer listicles lacking empirical validation.

In a banking environment, the cost of evaluating non-viable tools or adopting non-deterministic, unauditable solutions is exceptionally high:
1. **Security & IP Leakage:** Shipping proprietary source code, DB schemas, or test fixtures to third-party endpoints violates data boundary policies and bank secrecy regulations.
2. **CI/CD Pipeline Corruption:** Introducing stochastic, non-deterministic flaky test generators into automated deployment gates halts delivery velocities and degrades developer trust.
3. **Engineering Opportunity Cost:** Architect hours spent reviewing and attempting sandbox trials of superficial wrappers detract from core platform modernization.

### 1.2 Mission & Objective
The **AI Test Engineering Horizon Radar** is designed to replace manual, ad-hoc discovery with an autonomous, adversarial intelligence pipeline. It continuously monitors, extracts, adversarially audits, and clusters innovations strictly relevant to Software Quality Engineering (QE) and SDLC verification, producing deterministic viability rankings and an interactive Tech Radar.

---

## 2. Core Architectural Questions & Paradigms Considered

Designing this intelligence system requires making fundamental architectural trade-offs across four macro dimensions:

```mermaid
flowchart TD
    subgraph D1 ["Dimension 1: Workflow Execution Model"]
        M1["Option 1A: Event-Driven Microservices / Queues"]
        M2["Option 1B: Autonomous Multi-Agent Swarm / Choreography"]
        M3["Option 1C: Decoupled Stage DAG with Deterministic Checkpoints"]
    end

    subgraph D2 ["Dimension 2: Noise Filtration & Evaluation Topology"]
        E1["Option 2A: End-to-End LLM Firehose (LLM evaluates all)"]
        E2["Option 2B: Hybrid Heuristic Sieve + Adversarial LLM Critique"]
        E3["Option 2C: Multi-Persona Adversarial Committee (CISO, Platform, QE)"]
    end

    subgraph D3 ["Dimension 3: Deduplication & Redundancy Detection"]
        S1["Option 3A: Exact Match & URL Hashing"]
        S2["Option 3B: Semantic Vector Clustering (pgvector Cosine Distance)"]
    end
```

---

### Dimension 1: Workflow Execution & Pipeline Topology

#### Option 1A: Distributed Event-Driven Microservices (Kafka / Celery / RabbitMQ)
- **Concept:** Every ingestion source emits raw event streams into a distributed message broker; worker pools consume messages and process stages independently.
- **Pros:** Scalable to massive unbounded ingestion firehoses (millions of tweets, blogs, articles); decoupled autoscaling.
- **Cons & Failure Modes:** Extreme operational overhead (requires managing brokers, dead-letter queues, worker coordination, distributed tracing); significant deployment friction for an engineering intelligence tool designed to run locally or on modest scheduled compute. Over-engineered for curated ingestion of ~100–500 high-signal items per month.

#### Option 1B: Autonomous Multi-Agent Swarm / Dynamic Choreography (e.g., AutoGen, CrewAI)
- **Concept:** Dynamic agents interact autonomously in open-ended conversations, debating and assigning tasks to each other dynamically.
- **Pros:** Highly flexible emergent behaviors; agents can self-direct exploratory research.
- **Cons & Failure Modes:** Non-deterministic execution loops; runaway token and monetary costs; difficulty in reproducing exact scoring paths for auditing; risk of circular agent negotiations and deadlocks. Violates the strict enterprise requirement for deterministic repeatability and auditable scoring traces.

#### Option 1C (Proposed): Decoupled 4-Stage Directed Acyclic Graph (DAG) with Deterministic Intermediate Checkpoints
- **Concept:** A discrete 4-stage pipeline where data transitions through strictly typed states:
  $$\text{Raw Ingestion} \xrightarrow{\text{Stage 1: Noise Sieve}} \text{Filtered Signal} \xrightarrow{\text{Stage 2: Deep Extractor}} \text{Dossier} \xrightarrow{\text{Stage 3: Enterprise Skeptic}} \text{Critique} \xrightarrow{\text{Stage 4: Radar Categorizer}} \text{Radar Item}$$
- **Pros:** 
  - Predictable execution path with bounded token spend and finite termination.
  - Every stage can be tested in total isolation using unit tests and recorded fixtures.
  - Every stage boundary is persisted to PostgreSQL, allowing offline resumption, replayability, and point-in-time audits.
  - Can be driven either from a local CLI or scheduled via GitHub Actions / container cron jobs without infrastructure daemons.
- **Cons:** Less dynamic than an open-ended agent swarm; pipeline steps are fixed at design time.

---

### Dimension 2: Noise Filtration & Evaluation Topology

#### Option 2A: Pure LLM Firehose Evaluation
- Ingest everything and pass full texts immediately to a large reasoning model (e.g., Gemini 1.5 Pro / GPT-4o).
- **Failure Mode:** Extremely wasteful in token consumption; processing thousands of marketing blogs and vanity press releases wastes computational budget on low-density noise.

#### Option 2B (Proposed Baseline): Two-Tiered Hybrid (Deterministic Heuristic Sieve + Adversarial LLM Critique)
- **Tier 1 (Stage 1 Sieve):** Fast rule-based scoring (regex, domain reputation, keyword density, lack of code/paper link) computing early $Hype > 0.60$ drops before any LLM API call is made. Drops > 70% of low-density marketing at zero LLM cost.
- **Tier 2 (Stages 2 & 3):** Deep extraction and adversarial review applied only to qualified signals that pass the noise sieve.

#### Option 2C (Under Discussion): Multi-Persona Adversarial Committee
- Rather than a single "Enterprise Skeptic" prompt, Stage 3 executes three focused adversarial evaluators:
  1. **The CISO / Security Gate:** Egress risks, token leaks, secret handling in tests, third-party hosting risks.
  2. **The CI/CD Platform Architect:** Deterministic seed replay, flaky test injection risks, pipeline execution latency, runner requirements.
  3. **The Quality Engineering Director:** Test maintainability, mutation effectiveness, real-world defect detection capability vs synthetic vanity pass-rates.
- **Trade-off:** Triples Stage 3 LLM calls, but provides deeply differentiated, multi-perspective banking scrutiny.

---

### Dimension 3: Semantic Deduplication & Redundancy Clustering

#### Option 3A: URL & Metadata Hash Matching Only
- Detects exact reposts of the same link, but completely blind to the rampant phenomenon of "wrapper proliferation" (different vendors marketing the exact same generic prompt pattern or open-source wrapper under new brand names).

#### Option 3B (Proposed): Integrated Relational + Vector Persistence (`pgvector`)
- Ingested technical dossiers generate dense vector embeddings (1536 dims).
- When a new tool or paper is evaluated, the system executes an automated cosine distance query against historical dossiers:
  $$\text{Cosine Distance}(\vec{u}, \vec{v}) = 1 - \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\| \|\vec{v}\|}$$
- If a candidate signal has semantic similarity $> 0.88$ with an existing entry but provides no new architectural innovation or reproducible baseline, an automatic **Wrapper Penalty ($-0.20$)** is applied.

---

## 3. Decision Rationale & Selected Architecture

Following collaborative deliberation, the architecture formally locks into:
- **Dimension 1:** **Option 1C** (Decoupled 4-Stage Directed Acyclic Graph with Deterministic Intermediate Checkpoints).
- **Dimension 2:** **Option 2C** (Multi-Persona Adversarial Committee: CISO / Security Gate, CI/CD Platform Architect, Quality Engineering Director).
- **Dimension 3:** **Option 3B** (Unified PostgreSQL + pgvector Persistence for Semantic Clustering and Automated Wrapper Penalization).

### 3.1 The 3-Persona Adversarial Review Committee (Stage 3)
Instead of a single monolithic prompt, Stage 3 executes three discrete adversarial evaluators, each assessing candidate innovations from distinct enterprise banking governance mandates:

| Committee Persona | Mandate & Focus | Evaluation Criteria | Weight |
| :--- | :--- | :--- | :--- |
| **1. CISO / Security Architect** | Data egress boundaries, secrecy, credentials, compliance. | - Zero-egress VPC & on-prem / air-gapped readiness.<br>- Private source code, DB schema, or customer test data leakage.<br>- Secret / token scrubbing in synthetic fixtures. | **35%** |
| **2. CI/CD Platform Architect** | Determinism, runner economics, build gate reliability. | - Deterministic seed replayability (zero flaky test introduction).<br>- Runner compute overhead & container execution model.<br>- Flaky test quarantine & failure isolation mechanisms. | **35%** |
| **3. QE Director / Lead** | True defect discovery, test maintainability, resilience. | - Real-world defect detection vs synthetic vanity benchmarks.<br>- Assertion quality and locator robustness (anti-brittle).<br>- Test suite maintainability and contract/spec alignment. | **30%** |

#### Enterprise Viability Composite Formula:
$$E_v = 0.35 \cdot S_{\text{security}} + 0.35 \cdot S_{\text{cicd}} + 0.30 \cdot S_{\text{qe}}$$

Each persona independently generates:
1. Normalized score $S_i \in [0.0, 1.0]$.
2. Explicit risk flags and vulnerabilities.
3. Operational prerequisites for bank adoption.
4. Detailed critique reasoning.

### 3.2 Semantic Clustering & Wrapper Penalty (Stage 4 & pgvector)
During Stage 2, technical claim embeddings (1536 dims) are stored in `signal_dossiers.embedding`.
In Stage 4, before ring categorization:
1. An asynchronous cosine distance search queries existing dossiers:
   $$\text{Cosine Distance}(\vec{u}, \vec{v}) = 1 - \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\| \|\vec{v}\|}$$
2. If similarity $> 0.88$ (`WRAPPER_SIMILARITY_THRESHOLD`) with an existing entry, and the candidate fails to provide an independent open benchmark or distinct architectural mechanism:
   - An automatic **Wrapper Deduction ($-0.20$)** is applied to Signal Validity $S_v$.
   - The item is flagged: `"Flagged as wrapper / duplicate of [Existing Tool/Paper]"`.

```mermaid
flowchart TD
    subgraph Sources ["1. Curated Ingestion Layer"]
        S_ARXIV["arXiv cs.SE\n(Empirical Papers)"]
        S_GH["GitHub Trending / Metrics\n(Open-source velocity)"]
        S_BLOG["Tier-1 Tech Blogs\n(Enterprise Post-Mortems)"]
    end

    subgraph DB ["2. Unified Persistence (PostgreSQL 16 + pgvector)"]
        T_RAW[("ingested_sources\n(Raw Payloads + Noise Score)")]
        T_DOS[("signal_dossiers\n(Claims + pgvector Embeddings)")]
        T_EVAL[("enterprise_evaluations\n(CISO, CI/CD, QE Critiques)")]
        T_RADAR[("radar_items\n(Active Rings + Historical Deltas)")]
    end

    subgraph DAG ["3. Deterministic 4-Stage DAG Pipeline (1C)"]
        direction TB
        ST1["Stage 1: Noise Sieve\n(Heuristic filter; drops Hype > 0.60)"]
        ST2["Stage 2: Deep Extractor\n(Technical fact extraction + vectorization)"]
        
        subgraph Stage3 ["Stage 3: Multi-Persona Committee (2C)"]
            direction LR
            P_SEC["CISO / Security Gate\n(Weight: 35%)"]
            P_CICD["CI/CD Architect\n(Weight: 35%)"]
            P_QE["QE Director\n(Weight: 30%)"]
        end

        ST4["Stage 4: Radar Categorizer\n(Adopt/Trial/Assess/Hold placement +\npgvector Wrapper Detection (3B))"]

        ST1 -->|"Qualified Signals"| ST2
        ST2 -->|"Signal Dossier"| Stage3
        Stage3 -->|"Synthesized Critique"| ST4
    end

    Sources --> ST1
    ST1 -.->|"Persist & Checkpoint"| T_RAW
    ST2 -.->|"Dossier & Embedding"| T_DOS
    Stage3 -.->|"Audit Trail"| T_EVAL
    ST4 -.->|"Published State"| T_RADAR

    subgraph Presentation ["4. Decoupled Presentation Layer"]
        CLI["CLI Tool (`radar`)"]
        DIGEST["Markdown Executive Digest\n(`reports/YYYY-WW.md`)"]
        WEB["Interactive Radar SPA\n(Vite/React/Tailwind/D3)"]
    end

    T_RADAR --> CLI
    T_RADAR --> DIGEST
    T_RADAR --> WEB
```

---

## 4. Key Architectural Guarantees & Constraints

1. **Air-Gapped & Zero-Egress Compatibility:**
   The entire system must run with local LLM providers (Ollama / vLLM running Llama 3 / Mistral) and local containerized PostgreSQL (`podman compose up -d`), requiring zero internet egress for corporate/private evaluation batches.
2. **Deterministic Anti-Hype Deductions:**
   All scoring deductions (no dataset $-0.30$, synthetic-only $-0.25$, superficial wrapper $-0.20$, sponsored promo $-0.15$) and engineering bonuses (peer-reviewed $+0.30$, OSS velocity $+0.25$, enterprise case study $+0.20$) are mathematically computed and locked into an immutable audit trail.
3. **Decoupled Visualization:**
   The presentation layer (`web/`) is completely decoupled from the data pipeline, consuming static, versioned `radar.json` snapshots. This allows zero-cost, zero-maintenance hosting via GitHub Pages or enterprise internal static document servers.

---

## 5. Consequences & Trade-offs

### Positive Consequences
- **Predictable Compute & Bounded Cost:** Strict stage gating drops noisy payloads before any LLM invocations occur.
- **Auditability:** Every radar item links back to its exact raw source payload, deep extraction dossier, adversary critique, and vector similarity neighbors.
- **CI Parity & Testability:** The entire pipeline can execute end-to-end in mock mode without network access or LLM API keys during CI.

### Negative Consequences / Trade-offs
- Requires local Podman/PostgreSQL runtime for full stateful persistence.
- Curated ingestion boundaries mean sources must be explicitly maintained rather than crawling the open web indiscriminately.

---

## 6. Deliberation Outcome & Active Discussion Points

### Deliberation Resolution:
- **Decision on 1C (DAG):** Adopted. Guarantees deterministic state checkpoints and bounded costs.
- **Decision on 2C (Adversarial Committee):** Adopted. Replaces monolithic review with 3 banking personas (CISO: 35%, CI/CD: 35%, QE: 30%).
- **Decision on 3B (pgvector Deduplication):** Adopted. Detects wrapper redundancy via cosine distance $> 0.88$ with automatic $-0.20$ penalty.

### Next Topics for Review:
1. **Scope Boundaries for Quality Engineering:**
   - Defining inclusion vs. exclusion boundaries for adjacent SDLC tools (e.g. general coding agents vs. QE-specialized agents).
2. **Historical Trend Tracking & Ring Movements:**
   - Tracking delta score movements across bi-weekly runs.
