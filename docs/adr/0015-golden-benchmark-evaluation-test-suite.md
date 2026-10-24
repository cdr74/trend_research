# ADR 0015: Golden Benchmark Evaluation Test Suite and Regression Gates

## Status
Accepted

## Context
As the Trend Horizon Radar progresses through ingestion, Stage 1 noise sieving, Stage 2 fact extraction, Stage 3 topic convergence and multi-lens adversarial evaluation, and Stage 4 radar categorization, systemic regression testing is necessary. Small modifications to heuristic weights, prompt templates, similarity thresholds, or categorization matrices could allow marketing hype into `Adopt` rings (false positives) or relegate authentic engineering breakthroughs to `Hold` (false negatives).

Milestone 3 Task 6 establishes a deterministic, multi-channel Golden Benchmark test harness to validate end-to-end pipeline precision, recall, and scoring bounds without external network dependencies or token expenditures.

## Requirements & Constraints
1. **Curated Ground-Truth Dataset (20 Records):**
   - **10 High-Signal Verified Innovations:** Spanning academic pre-prints (arXiv), open-source repositories (GitHub), and practitioner engineering post-mortems (RSS). Covering all 6 QE domain pillars (`Spec & Model`, `Test Synthesis`, `Execution & Optimization`, `Triage & Self-Healing`, `Agent Systems`, `Governance & Evals`).
   - **10 Marketing Hype & Parasitic Wrapper Products:** Spanning hyperbolic claims ("100x faster", "replaces all engineers"), defect guarantees ("100% bug free"), commercial affiliate monetization, superficial LLM repackaging without novel architecture, and vanity benchmark listicles.
2. **End-to-End Pipeline DAG Validation:**
   - Exercise the full 4-stage pipeline:
     $$\text{SourcePayload} \xrightarrow{\text{Stage 1: Noise Sieve}} \text{QualifiedSignal} \xrightarrow{\text{Stage 2: Deep Extractor}} \text{SignalDossier} \xrightarrow{\text{Stage 3: Convergence \& Committee}} \text{TrendTopic \& EnterpriseEvaluation} \xrightarrow{\text{Stage 4: Categorizer}} \text{RadarItem}$$
3. **Acceptance Threshold Gates:**
   - **Precision (Zero Hype Leakage):** 0% of hype/wrapper products may enter `Adopt`, `Trial`, or `Assess`. They must either be dropped early by Stage 1 ($> 0.60$ noise score) or categorized into `Hold` ($H > 0.60$ or wrapper penalty).
   - **Recall (Zero Innovation Erasure):** 100% of high-signal innovations must pass Stage 1 noise sieving and receive an enterprise ring of `Adopt`, `Trial`, or `Assess`.
   - **Score Bounds:** $0.0 \le S_v \le 1.0$, $0.0 \le H \le 1.0$, $0.0 \le E_v \le 1.0$.
4. **Hermetic Offline Execution:**
   - Must run in CI/CD and local development environments without network access or paid API keys using deterministic providers.

## Options Considered

### Option 1: Live API Golden Evals against Frontier Models
- Query live LLMs (Gemini / OpenAI) on every CI run against web search results.
- *Pros:* Tests frontier model reasoning drift.
- *Cons:* Flaky, high latency, expensive token consumption, vulnerable to rate limits and upstream outages; violates CI reproducibility directives.

### Option 2: Deterministic In-Memory Golden Benchmark Suite (Selected)
- A dedicated fixture dataset of 20 categorized payloads.
- Runs through the actual pipeline stage classes (`NoiseSieve`, `DeepExtractor`, `TopicConvergenceEngine`, `MultiLensEvaluator`, `RadarCategorizer`) with deterministic vector generation and mock structured response contracts.
- *Pros:* Instant execution (< 1s), 100% deterministic, zero cost, reproducible in any CI runner.
- *Cons:* Requires periodic curation as new industry buzzwords emerge.

## Decision Rationale
We adopt **Option 2**. The benchmark harness is implemented in `tests/integration/test_golden_benchmark.py` and supported by `data/fixtures/golden_benchmark.json`.

## Consequences

### Positive
- Strict regression defense guarding the integrity of the Tech Radar.
- Guarantees 0% false positives for hype spam and 0% false negatives for genuine breakthroughs.
- Continuous parity between specification contracts and pipeline execution.
- Enables safe refactoring of prompt templates and threshold configurations.

### Negative / Trade-offs
- Dataset must be periodically maintained and expanded as new marketing patterns arise.
