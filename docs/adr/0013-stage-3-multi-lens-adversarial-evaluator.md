# ADR 0013: Stage 3 Multi-Lens Adversarial Evaluator Committee

## Status
Accepted

## Context
Following Stage 2 Deep Extraction (ADR-0011) and Topic Convergence (ADR-0012), signals are clustered into technical trends with verifiable claims and evidence tiers. However, technical novelty alone does not guarantee enterprise viability. Many AI-driven test engineering tools fail in real-world deployment due to security vulnerabilities (uncontrolled code/data egress, secret leakage), operational unreliability (non-deterministic test execution, excessive GPU/memory footprints, flaky runners), or synthetic vanity benchmarking (solving contrived puzzles rather than industrial software engineering bugs).

To protect enterprise adoption decisions, Stage 3 introduces a rigorous, multi-lens adversarial evaluation committee (Option 2C / Dimension 2 in ADR-0000).

## Requirements & Constraints
1. **Three Discrete Architectural Lenses:**
   - **Security & Privacy Lens (Weight: 35%):** Evaluates egress boundaries, VPC isolation, zero-trust constraints, air-gapped LLM compatibility, and credential/secret masking.
   - **Operational Feasibility & CI/CD Lens (Weight: 35%):** Evaluates test replayability, seed determinism, compute/GPU resource footprint, CI runner latency, and maintenance friction.
   - **Technical Rigor & Empirical Problem-Solving Lens (Weight: 30%):** Evaluates whether the innovation solves genuine production software engineering defects vs trivial synthetic benchmarks, and checks methodology repeatability.
2. **Deterministic Composite Viability Score ($E_v$):**
   $$E_v = 0.35 \cdot S_{\text{sec}} + 0.35 \cdot S_{\text{ops}} + 0.30 \cdot S_{\text{tech}}$$
   Weights must be configurable in `Settings` (`RADAR_SECURITY_WEIGHT`, `RADAR_CICD_WEIGHT`, `RADAR_QE_WEIGHT`) and sum to 1.0.
3. **Structured Audit Contracts:**
   - LLM generation must conform to `CommitteeAuditResult` (sub-scores in $[0.0, 1.0]$, lens critiques, enterprise risk flags, and prerequisites).
   - Must assemble an immutable `EnterpriseEvaluation` tied to `SignalDossier.id`.
4. **Single Multi-Perspective Turn (Option B):**
   - Execute evaluation in a single structured prompt turn incorporating the three adversarial personas to maximize latency and cost efficiency, especially for local CLI execution (`AgyCliProvider`).
5. **Hermetic Offline Verification:**
   - Unit tests must execute deterministically without network access using `MockProvider`.

## Options Considered

### Option A: Three Independent Sequential/Parallel LLM Calls
- Make 3 separate API calls (one for Security, one for Ops, one for QE), followed by a 4th aggregation call.
- *Pros:* Complete isolation of persona system prompts.
- *Cons:* 3-4x latency, 3-4x token spend, complex failure modes; prohibitive for high-throughput batch evaluation.

### Option B: Single Multi-Perspective Structured Evaluation Turn (Selected)
- A single comprehensive prompt instructing the LLM to inspect the dossier sequentially through the 3 adversarial personas, outputting structured sub-scores, critiques, risk flags, and prerequisites in one validated JSON payload.
- *Pros:* High throughput, minimal latency, single token round-trip, cohesive cross-lens synthesis in the final consensus critique.
- *Cons:* Requires a detailed, well-structured system prompt defining each persona's strict rubric.

## Decision Rationale
We adopt **Option B**. The `MultiLensEvaluator` is implemented in `src/radar/pipeline/evaluator.py`.

Key Architecture Specifications:
1. **Evaluation Schema (`CommitteeAuditResult`):**
   - Strictly bounded sub-scores: `security_score`, `cicd_score`, `qe_score`.
   - Explicit critique strings for each lens: `security_critique`, `cicd_critique`, `qe_critique`, `skeptic_critique`.
   - String lists for `enterprise_risks` and `prerequisites`.
2. **Formula Calculation:**
   - `composite_viability_score` is computed deterministically in Python using the configured weights, preventing model arithmetic hallucinations.
3. **Persistence:**
   - Persisted to PostgreSQL using `RadarRepository.save_evaluation()`.

## Consequences

### Positive
- Strict, adversarial audit of AI test tools against real enterprise banking and defense constraints.
- Identifies critical failure modes before pilot adoption (e.g. non-deterministic assertions, cloud egress).
- Deterministic, mathematically bounded viability scoring.
- Zero extra latency or API spend compared to multi-agent swarm approaches.

### Negative / Trade-offs
- Highly novel paradigms with zero precedent may receive conservative initial operational scores until practitioner post-mortems validate them.
