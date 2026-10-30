# ADR 0028: Canonical Exemplar Consolidation and Open-Source Traction Sieve

## Status
Proposed (Pending Operator Approval)

## Context
As the Trend Horizon Radar ingestion corpus expanded to over 312 evaluated items across 15 active source streams, two distinct challenges in information density emerged:

1. **Low-Traction Open-Source Noise in Stage 1:**
   - Analysis of the 239 GitHub items in the evaluated corpus revealed that 55 repositories had an engagement velocity of `0.0`, and another 102 repositories had a velocity `< 5.0` with fewer than 25 stars.
   - Many of these payloads represent student coursework, personal learning notes (e.g. `sergiparpal/mutation-study`), or abandoned weekend experiments (e.g. `lunox-work/duediligence`).
   - Passing these repositories through Stage 2 (Deep Extractor) and Stage 3 (Adversarial Evaluator) expends LLM token quota and adds unnecessary clutter without providing actionable enterprise intelligence.

2. **Visual and Cognitive Clutter from Topic Oversaturation:**
   - Even when tools are legitimate, high-volume topics exhibit extreme blip density on the radar:
     - `Autonomous Browser & UI Agent Systems`: 121 blips
     - `Automated Mutation Testing & Fault Injection`: 92 blips
   - In `Automated Mutation Testing`, for example, the radar displays 5 separate blips for the Stryker project suite (`stryker-js`, `stryker-net`, `stryker4s`, `mutation-testing-elements`, `azure-devops-mutation-testing`) and 3 separate blips for Pitest (`pitest`, `gradle-pitest-plugin`, `pitest-descartes`).
   - In an executive ThoughtWorks-style radar, a blip is expected to represent a **curated technological concept, canonical framework, or breakthrough technique**—not an exhaustive catalog of every plugin, multi-language wrapper, and fork.

---

## Decision Matrix & Multi-Tiered Architecture

We resolve this tension between **executive readability** and **exhaustive intelligence** through a hybrid three-tier strategy spanning ingestion, pipeline consolidation, and interactive UI filtering.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TIER 1: STAGE 1 MINIMUM TRACTION GATE (Heuristic Noise Sieve)               │
│ - Drops 0-star repos, student coursework, and abandoned experiments         │
│ - Requires stars >= 25 OR velocity >= 5.0 for GitHub payloads                │
│ - Exempts verified academic peer-reviewed repositories                      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Qualified Signals
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ TIER 2: STAGE 4 CANONICAL EXEMPLAR CONSOLIDATION (Categorizer & Export)     │
│ - Groups evaluated items by converged TrendTopic                            │
│ - Computes Exemplar Ranking (Ring priority + Viability + Velocity)          │
│ - Elects Top K (3-5) Canonical Exemplars (is_canonical = True)              │
│ - Rolls remainder into corroborating_sources & corroboration_count          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ radar.json bundle
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ TIER 3: WEB DASHBOARD DUAL PERSPECTIVE & VELOCITY CONTROLS (web/)           │
│ - Executive Radar View: Displays Top Canonical Exemplars (~40 blips)        │
│ - Full Intelligence View: Toggle to inspect all 300+ evaluated signals      │
│ - Filter Ergonomics: Minimum Velocity slider & Corroborating Evidence modal │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1. Tier 1: Stage 1 Minimum Traction Gate for Open-Source Repositories (`noise_sieve.py`)
- **Mechanism:** In `NoiseSieve.evaluate()`, inspect payloads where `payload.source_type == SourceType.GITHUB`.
- **Thresholds:**
  - `min_github_stars`: Default 25.
  - `min_github_velocity`: Default 5.0.
- **Rule:** If `stars < min_github_stars` AND `velocity < min_github_velocity`:
  - **Exemption:** The signal is exempt if it possesses verified academic or institutional authority (`authority_weight >= 1.5` or explicit peer-reviewed paper markers).
  - Otherwise, the payload fails Stage 1 with rejection reason:
    `"Insufficient open-source traction (stars < 25 and velocity < 5.0)"`.
- **Benefit:** Instantly halts ~150 zero-traction repos at the heuristic stage, saving substantial LLM token cost during automated evaluation.

### 2. Tier 2: Stage 4 Canonical Exemplar Selection & Evidence Roll-Up (`categorizer.py`)
- **Data Model Contract:**
  - Add `is_canonical: bool = Field(default=True)` to `RadarItem` (domain model) and `RadarItemTable` (SQLAlchemy schema).
- **Consolidation Algorithm:**
  - In `RadarCategorizer.categorize_batch()` (and export generation), partition items by `topic_name` / `topic_id`.
  - For topics containing $> K$ items (default $K = 4$):
    - Compute an **Exemplar Composite Score**:
      $$\text{Score} = \text{RingWeight} \times 0.40 + \text{ViabilityScore} \times 0.35 + \text{NormalizedVelocity} \times 0.25$$
      *(where Adopt=4, Trial=3, Assess=2, Hold=1)*.
    - Elect top $K$ items as canonical (`is_canonical = True`), ensuring distinct namespace/ecosystem coverage (e.g. Stryker for JS/.NET, Pitest for JVM, Mutmut for Python).
    - Designate remaining topic members as non-canonical (`is_canonical = False`).
    - **Evidence Aggregation:** Append the names and URLs of non-canonical topic members to the `corroborating_sources` list and increment `corroboration_count` for the canonical exemplars. Zero intelligence is lost.

### 3. Tier 3: Web Dashboard Dual Perspective & Ergonomics (`web/`)
- **Executive Mode vs. Full Intelligence Toggle:**
  - Top-level pill toggle in `web/src/App.tsx`:
    - `[★ Executive Radar (Top Exemplars)]` (Active by default)
    - `[🌐 Full Intelligence (All Signals)]`
  - In Executive Mode, items are filtered by `item.is_canonical !== false`.
  - Sub-header status counter explicitly shows:
    `"Showing 42 Canonical Exemplars (filtered from 312 total signals)"` with a quick link to show all.
- **Filter Sidebar & Modal Details:**
  - Add **Minimum Velocity** filtering options in `FilterSidebar.tsx`.
  - In `ItemDetailModal.tsx`, render a structured section:
    `"Corroborating Implementations & Community Tools"` listing the related non-canonical frameworks rolled into that technique.

---

## Consequences

### Positive
- **Executive Clarity:** Default radar view drops from 312 blips down to ~40 high-signal, canonical technologies, matching the clarity of the ThoughtWorks Tech Radar.
- **Deep Intelligence Preserved:** Every single evaluated tool, paper, and repository remains in the PostgreSQL database and is accessible in the UI via the "Full Intelligence" toggle or Matrix Table.
- **Resource Efficiency:** Low-traction GitHub noise is rejected at Stage 1 before costly LLM extraction and adversarial evaluation.
- **Data Model Traceability:** Full backward compatibility with existing `radar.json` consumers; `is_canonical` defaults to `true`.

### Negative / Trade-offs
- A brand-new, cutting-edge open-source repository published less than 48 hours ago might have < 25 stars and < 5.0 velocity.
  - *Mitigation:* Can be manually ingested via `radar ingest` with `authority_weight >= 1.5`, or linked to an arXiv pre-print which bypasses the GitHub star gate. Thresholds are configurable via environment variables (`RADAR_GITHUB_MIN_STARS`).
