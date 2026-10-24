# ADR 0012: pgvector Topic Convergence, Cross-Source Corroboration, and Wrapper Detection

## Status
Accepted

## Context
Following Stage 2 Deep Extraction (ADR-0011), each processed signal yields a strictly validated `SignalDossier` containing technical claims, evidence tiers, artifact verification booleans, and a 1536-dimensional dense semantic embedding.

Signals in isolation cannot reveal macro-industry trajectories or distinguish authentic technological breakthroughs from derivative marketing wrappers. To produce trustworthy intelligence, the radar must identify when independent source channels (academic pre-prints, open-source codebases, and practitioner production post-mortems) converge on the same core problem or architectural pattern.

Furthermore, commercial vendors frequently repackage existing open-source libraries or foundational model prompts with proprietary branding and hyperbolic claims. The radar must deterministically detect these parasitic wrappers and penalize them to prevent radar distortion.

## Requirements & Constraints
1. **Configurable Thresholds:** Convergence and wrapper detection thresholds must not be hardcoded magic numbers; they must be configurable via `Settings` (`RADAR_TOPIC_CONVERGENCE_THRESHOLD`, `RADAR_WRAPPER_SIMILARITY_THRESHOLD`, `RADAR_WRAPPER_PENALTY`, `RADAR_CORROBORATION_CONSENSUS_BONUS`).
2. **Semantic Similarity Metric:** Measure cosine similarity ($1.0 - \text{cosine\_distance}$) over 1536-dimensional embeddings:
   - Topic Convergence: $\text{Cosine Similarity} \ge \tau_{\text{converge}}$ (default: $0.82$).
   - Parasitic Wrapper Scrutiny: $\text{Cosine Similarity} \ge \tau_{\text{wrapper}}$ (default: $0.88$).
3. **LLM Topic Synthesis:** When merging signals into a `TrendTopic` cluster, invoke the configured `LLMProvider` to synthesize a unified canonical name and 2-3 sentence technical summary reflecting the aggregated advances across all member dossiers.
4. **Cross-Source Corroboration Bonus:** When a converged topic spans $\ge 3$ distinct source channels (e.g. arXiv + GitHub + RSS), apply an automated multi-source consensus bonus ($+0.25$ to topic validity, clamped to $1.0$).
5. **Parasitic Wrapper Penalty:** When an incoming signal matches an existing dossier with similarity $\ge \tau_{\text{wrapper}}$ and lacks independent empirical artifacts (`not has_reproducible_benchmark` and `not has_open_source_repo`, or `is_superficial_wrapper`), flag the dossier as a wrapper and apply an automated $-0.20$ validity penalty.
6. **Dual Execution Runtime:** Must support both PostgreSQL + `pgvector` database queries and an in-memory cosine fallback for fast, offline unit testing without database dependencies.

## Options Considered

### Option 1: Exact String / Keyword Overlap
- Group dossiers sharing identical keywords, tool names, or tags.
- *Pros:* Simple, zero embedding dependency.
- *Cons:* Fragile; fails on synonymy, differing research paper titles for the same concept, or vendor rebranding of open-source tools.

### Option 2: Pre-computed Fixed Cluster Centroids
- Cluster signals into a pre-defined static ontology of topics.
- *Pros:* Fast fixed-bucket assignment.
- *Cons:* Incapable of discovering emerging architectural paradigms that do not fit predefined taxonomy bins.

### Option 3: Dynamic Embedding Convergence with LLM Synthesis & Wrapper Scrutiny (Selected)
- Dynamically match incoming embeddings against existing dossiers using `pgvector` cosine similarity.
- Assign dossiers to existing `TrendTopic` clusters or instantiate new clusters.
- Prompt the LLM provider to synthesize/update the topic's canonical title and summary as new evidence arrives.
- Apply deterministic mathematical adjustments (consensus bonus $+0.25$, wrapper penalty $-0.20$).
- *Pros:* Fully autonomous, semantic, dynamic topic evolution; robust defense against parasitic marketing wrappers.
- *Cons:* Requires vector similarity calculations and an additional structured LLM synthesis call when topics merge.

## Decision Rationale
We adopt **Option 3**. The `TopicConvergenceEngine` is implemented in `src/radar/pipeline/convergence.py`.

Key Architecture Specifications:
1. **Configurable Settings (`src/radar/core/config.py`):**
   - `topic_convergence_threshold: float = 0.82`
   - `wrapper_similarity_threshold: float = 0.88`
   - `wrapper_penalty: float = 0.20`
   - `corroboration_consensus_bonus: float = 0.25`
2. **Topic Synthesis Contract (`SynthesizedTopic`):**
   - Pydantic v2 schema capturing `name`, `summary`, and consensus `primary_category`.
   - Prompt synthesizes technical convergence across all member dossiers.
3. **Corroboration Multiplier:**
   - Multi-channel source diversity is determined by counting unique source channels (`SourceType.ARXIV`, `SourceType.GITHUB`, `SourceType.RSS`).
   - $\ge 3$ unique channels awards $+0.25$ consensus validity bonus.
4. **Wrapper Detection Rules:**
   - $\text{Cosine Similarity} \ge \tau_{\text{wrapper}}$ ($0.88$).
   - Condition: Incoming signal has no reproducible benchmark and no public open source repository, or is explicitly flagged as a superficial wrapper.
   - Consequence: Flagged as parasitic wrapper with wrapper penalty deducted from validity.

## Consequences

### Positive
- Autonomous discovery and clustering of converging industry trends.
- Automated defense against deceptive wrapper products and marketing repackaging.
- High-quality, unified LLM summaries for executive and practitioner radar views.
- Fully offline testable with `MockProvider` and mathematical vector fixtures.

### Negative / Trade-offs
- Re-synthesizing topic summaries on every merge adds LLM turns for large clusters; mitigated by optional caching or debounced batch synthesis.
