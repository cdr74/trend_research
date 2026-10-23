# Project Intent & Architectural Design: AI Test Engineering Horizon Radar

## 1. Executive Summary & Objective

### 1.1 Context
In the wake of rapid generative AI and agentic tooling proliferation across the Software Development Life Cycle (SDLC), engineering leadership is inundated with marketing claims, superficial wrappers, and ephemeral hype. In high-governance financial enterprise environments (e.g., Tier-1 global investment banking and wealth management), the cost of evaluating non-viable tools or adopting non-deterministic, un-auditable solutions is exceptionally high.

### 1.2 Mission
Build an autonomous intelligence engine—the **AI Test Engineering Horizon Radar**—that filters, evaluates, and clusters SDLC and Quality Engineering (QE) innovations. The system replaces passive browsing with deterministic signal extraction, adversarial skepticism, and automated enterprise readiness scoring.

### 1.3 Key Outcomes
- **Zero-Hype Signal Isolation:** Algorithmic penalization of vanity metrics, unverified benchmarks, and affiliate-driven content.
- **Enterprise-First Vetting:** Automated evaluation of data privacy, VPC/air-gapped compliance, deterministic replayability, and integration feasibility with enterprise-scale architectures.
- **Actionable Decision Velocity:** Structured bi-weekly intelligence briefings and a dynamic ThoughtWorks-style Tech Radar (Adopt / Trial / Assess / Hold) focused specifically on Software Quality and Test Engineering.

---

## 2. Domain Scope & Taxonomy

The radar monitors advancements across six core SDLC QE pillars:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        SDLC QE HORIZON RADAR                           │
├──────────────────┬──────────────────┬──────────────────────────────────┤
│ 1. Spec & Model  │ 2. Test Synth    │ 3. Execution & Optimization      │
│  - Spec-to-test  │  - E2E / API     │  - Mutation testing              │
│  - Formal verif. │  - Synthetic gen │  - Predictive test selection     │
│  - Edge-case LLM │  - Mocking / TDM │  - Flaky test auto-isolation     │
├──────────────────┼──────────────────┼──────────────────────────────────┤
│ 4. Triage & Fix  │ 5. Agent Systems │ 6. Governance & Evals            │
│  - RCA agents    │  - Browser-use   │  - LLM-as-a-Judge test suites    │
│  - Self-healing  │  - CLI agents    │  - Safety / Prompt regression    │
│  - Auto-PR patch │  - Multi-agent QE│  - Determinism & audit trails    │
└──────────────────┴──────────────────┴──────────────────────────────────┘
```

---

## 3. System Architecture

The radar operates as a directed acyclic pipeline (DAG) with four decoupled stages: Ingestion, Noise Filtering, Adversarial Critique, and Synthesis.

```
                  ┌─────────────────────────────────┐
                  │       Source Ingestion          │
                  │ (ArXiv, GitHub, RSS, Curated)   │
                  └────────────────┬────────────────┘
                                   │ Raw Payloads
                                   ▼
                  ┌─────────────────────────────────┐
                  │     Stage 1: Noise Sieve        │
                  │   (Heuristic & Pattern Drop)    │
                  └────────────────┬────────────────┘
                                   │ Qualified Signals (Hype < 0.6)
                                   ▼
                  ┌─────────────────────────────────┐
                  │    Stage 2: Deep Extractor      │
                  │ (Spec, Claims, Code/Paper Fact) │
                  └────────────────┬────────────────┘
                                   │ Structured Signal Dossier
                                   ▼
                  ┌─────────────────────────────────┐
                  │  Stage 3: Enterprise Skeptic    │
                  │   (Adversarial Bank Architect)  │
                  └────────────────┬────────────────┘
                                   │ Scored Evaluation
                                   ▼
                  ┌─────────────────────────────────┐
                  │  Stage 4: Radar Categorizer     │
                  │ (Adopt/Trial/Assess/Hold + DB)  │
                  └─────────────────────────────────┘
```

---

## 4. Evaluation Rubric & Scoring Heuristics

Every ingested item is evaluated on a composite 0.0 to 1.0 scoring index across two axes: **Signal Validity** and **Enterprise Viability**.

### 4.1 Anti-Hype Penalties (Signal Validity Deductions)
- **$-0.30$:** Absence of reproducible benchmark, raw dataset, or source repository.
- **$-0.25$:** Exclusive reliance on synthetic vanity metrics (e.g., "99% automated bug fixing" evaluated only on trivial synthetic repos).
- **$-0.20$:** "Wrapper" architecture (direct un-augmented wrapper around standard proprietary LLMs without workflow, validation, or state-management innovations).
- **$-0.15$:** Sponsored / influencer promotional placement without peer or practitioner review.

### 4.2 Positive Engineering Signals (Signal Validity Bonuses)
- **$+0.30$:** Peer-reviewed empirical publication (e.g., IEEE TSE, ACM ICSE, ISSTA, arXiv SE) with reproducible artifact evaluation.
- **$+0.25$:** Active open-source commit velocity, high issue-to-resolution ratio, and open contributor base.
- **$+0.20$:** Production case studies or post-mortems from high-scale engineering organizations detailing edge-case failure modes.

### 4.3 Enterprise Viability Filter (Banking / Regulated Constraints)
The **Enterprise Skeptic** evaluates signals against 4 mandatory gates:
1. **Deployment Topology:** Can the model/tool operate within a zero-egress VPC, self-hosted, or on-prem environment?
2. **Deterministic Reproducibility:** Does the tool introduce non-deterministic flakiness into CI/CD gates, or does it enforce deterministic seeds/replayability?
3. **Data Security & Privacy:** Does operation require shipping proprietary source code, schema definitions, or test payloads to third-party endpoints?
4. **Auditability:** Does it produce human-inspectable reasoning traces suitable for audit and regulatory compliance?

---

## 5. Structured Data Schema

The pipeline guarantees strictly-typed data interchange between agents using JSON schema definitions.

### 5.1 Signal Entity Schema (`signal.schema.json`)
```json
{
  "$id": "https://radar.internal/schemas/signal.json",
  "type": "object",
  "required": [
    "id",
    "name",
    "category",
    "source_url",
    "hype_score",
    "viability_score",
    "recommended_ring",
    "key_innovation",
    "enterprise_risks",
    "evidence_tier"
  ],
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "name": { "type": "string" },
    "category": {
      "type": "string",
      "enum": [
        "Spec & Model",
        "Test Synthesis",
        "Execution & Optimization",
        "Triage & Self-Healing",
        "Agent Systems",
        "Governance & Evals"
      ]
    },
    "source_url": { "type": "string", "format": "uri" },
    "evidence_tier": {
      "type": "string",
      "enum": ["Academic Peer-Reviewed", "Open Source Repo", "Engineering Post-Mortem", "Vendor Announcement"]
    },
    "hype_score": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
    "viability_score": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
    "recommended_ring": {
      "type": "string",
      "enum": ["Adopt", "Trial", "Assess", "Hold"]
    },
    "key_innovation": { "type": "string" },
    "enterprise_risks": {
      "type": "array",
      "items": { "type": "string" }
    },
    "prerequisites": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

---

## 6. Implementation Roadmap

### Phase 1: Repository Baseline & Contracts (Sprint 1)
- [ ] Initialize repository structure and configuration with `agy`.
- [ ] Define JSON schemas for Signal, Evaluation Dossier, and Tech Radar structures.
- [ ] Configure environment dependencies (Python 3.11+, Pydantic v2, Ruff, Pytest).
- [ ] Establish initial static seed list of high-signal feeds (arXiv RSS, GitHub Trending targets, Tier-1 tech blogs).

### Phase 2: Ingestion & Filter Engine (Sprint 2)
- [ ] Implement asynchronous source ingestors (arXiv `cs.SE`, GitHub GraphQL, RSS feeds).
- [ ] Implement Stage 1 Rule-based Triager (noise sieve using deterministic keyword and metadata penalties).
- [ ] Persist normalized payloads to local storage (`data/raw/`).

### Phase 3: Adversarial LLM Evaluation Pipeline (Sprint 3)
- [ ] Implement Stage 2 Deep Extraction Agent with structured schema output.
- [ ] Implement Stage 3 Enterprise Skeptic Agent with banking-grade constraint prompting.
- [ ] Implement Stage 4 Radar Categorizer assigning `Adopt | Trial | Assess | Hold`.
- [ ] Unit and snapshot test evaluation agents against a curated benchmark set (10 high-value papers vs. 10 hype products).

### Phase 4: Output Synthesis & Radar Dashboard (Sprint 4)
- [ ] Generate automated Markdown/HTML bi-weekly digest (`reports/YYYY-WW.md`).
- [ ] Generate static interactive Radar UI (e.g., using ThoughtWorks open-source Radar generator or standalone lightweight visualization).
- [ ] Configure local CLI query tool (`radar query --category "Test Synthesis" --ring Trial`).

---

## 7. Operational Guidelines & Anti-Goals

### Non-Goals (What We Will NOT Build)
- **Generic AI News Aggregator:** We do not aggregate general LLM news, funding announcements, or general consumer tech. Focus is strictly on SDLC, Software Quality, and Test Engineering.
- **Autonomous Unsupervised Tool Adopter:** The agent does not execute or install unknown third-party software into our environments; it outputs evaluation intelligence for human engineering decision-making.
- **Unbounded Web Scraper:** Ingestion is bounded to curated, high-density professional and academic channels to prevent polluting vector/embedding stores with search-engine-optimized spam.