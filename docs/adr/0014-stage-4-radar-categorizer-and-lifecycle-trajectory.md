# ADR 0014: Stage 4 Radar Categorizer and Lifecycle Trajectory

## Status
Accepted (Amended by ADR-0022: Multi-Gated Deterministic Radar Categorization and Ranking)

## Context
In the 4-stage processing DAG established in ADR-0000, Stage 4 (Radar Categorizer) synthesizes all preceding stages:
1. Stage 1 (Noise Sieve): Initial heuristic noise filtering.
2. Stage 2 (Deep Extractor): Objective technical claims, domain classification, and vector embeddings.
3. Stage 3 (Topic Convergence & Multi-Lens Committee): Semantic clustering, corroboration consensus, parasitic wrapper penalties, and multi-lens viability scores ($E_v$).

Stage 4 must produce the final published intelligence entity: `RadarItem`. This requires:
1. **Signal Validity Score ($S_v$) and Hype Score ($H$):** Deterministic calculation combining anti-hype deductions and engineering bonuses.
2. **Tech Radar Ring Assignment:** Placement into one of 4 canonical ThoughtWorks-style rings (`Adopt`, `Trial`, `Assess`, `Hold`).
3. **Lifecycle Trajectory:** Classification into `Emerging`, `Consolidated`, or `Fading` based on time-decayed audience velocity and cross-channel corroboration.

## Requirements & Constraints
1. **Deterministic Validity & Hype Scoring:**
   - Baseline validity starts at $0.50$.
   - **Anti-Hype Deductions:**
     - $-0.30$: No reproducible benchmark, raw dataset, or public code repository.
     - $-0.20$: Parasitic or superficial wrapper architecture.
     - $-0.15$: Commercial vendor promotional announcement without peer review.
   - **Engineering & Convergence Bonuses:**
     - $+0.30$: Academic peer-reviewed publication with reproducible artifacts.
     - $+0.25$: Independent cross-source corroboration ($N_{\text{sources}} \ge 3$ or multi-source consensus).
     - $+0.20$: High open-source engagement velocity ($\text{velocity} \ge 25.0$).
     - $+0.20$: Production post-mortem from a recognized engineering team.
   - Clamp $S_v$ to $[0.0, 1.0]$.
   - Composite Hype Score: $H = \text{round}(1.0 - S_v, 4)$.
2. **Tech Radar Ring Decision Matrix:**
   - **Adopt:** Production ready. High viability ($E_v \ge 0.75$), low hype ($H \le 0.35$), backed by verifiable artifacts (benchmark, repo, or post-mortem).
   - **Trial:** Low-risk pilot. High viability ($E_v \ge 0.65$), moderate hype ($H \le 0.50$).
   - **Assess:** High potential or accelerating emergence. Viability $E_v \ge 0.45$, or high velocity ($v \ge 25.0$) warranting enterprise tracking.
   - **Hold:** High risk / unproven / marketing wrapper. Viability $E_v < 0.45$, or excessive hype ($H > 0.60$), or flagged as superficial wrapper.
3. **Lifecycle Trajectory:**
   - **Emerging:** High velocity ($\text{velocity} \ge 25.0$) with low cumulative volume or rising corroboration.
   - **Consolidated:** High corroboration ($N_{\text{sources}} \ge 3$) or steady proven track record ($5.0 \le \text{velocity} < 25.0$).
   - **Fading:** Stagnant velocity ($\text{velocity} < 5.0$) with declining activity or unaddressed hype penalties.
4. **Configurable Thresholds:** Cut-off parameters must be defined in `Settings` (`src/radar/core/config.py`).
5. **Decoupled CLI & Presentation:** Output published radar items to interactive CLI tables, JSON/CSV exports, and PostgreSQL persistence.

## Options Considered

### Option 1: LLM-Judged Final Ring Placement
- Ask the LLM to output "Adopt", "Trial", "Assess", or "Hold" in free text or structured JSON.
- *Pros:* Contextual flexibility.
- *Cons:* Non-deterministic, prone to hallucination, opaque scoring drift; undermines the objective mathematical integrity of the radar.

### Option 2: Deterministic Rule Matrix and Mathematical Bounds (Selected)
- Synthesize the mathematical scores from Stages 1-3 through strict deterministic formulas.
- Explicit threshold gates for rings and lifecycle stages.
- *Pros:* 100% deterministic, fully auditable, mathematically bounded, fast, and completely reproducible across environments.
- *Cons:* Requires calibrated thresholds; mitigated by placing parameters in configurable `Settings`.

## Decision Rationale
We adopt **Option 2**. The `RadarCategorizer` is implemented in `src/radar/pipeline/categorizer.py`.

## Consequences
### Positive
- Fully auditable decision trail for every item on the Radar.
- Mathematical consistency between viability, hype, ring, and trajectory.
- Clear separation between LLM semantic analysis and deterministic scoring rules.
- Fast, hermetic testing with deterministic fixtures.

### Negative / Trade-offs
- Edge cases near boundary thresholds (e.g. $E_v = 0.749$) require clear rule transparency in the generated critique and report.
