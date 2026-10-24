# ADR 0009: Stage 1 Deterministic Heuristic Noise Sieve

## Status
Accepted

## Context
The Trend Horizon Radar ingests hundreds of raw signals daily across academic pre-prints, open-source repositories, and practitioner feeds. Passing every raw signal directly into LLM-driven deep fact extraction (Stage 2) and adversarial committee evaluation (Stage 3) is both cost-prohibitive and computationally inefficient. Furthermore, content from public feeds frequently includes sponsored listicles, affiliate spam, marketing vaporware, and unsubstantiated claims ("replaces all developers", "zero bugs guaranteed").

To protect LLM token budgets and prevent synthetic marketing vanity from polluting the radar corpus, the pipeline introduces **Stage 1: Heuristic Noise Sieve**.

## Requirements & Constraints
1. **Zero LLM Token Footprint:** Stage 1 must execute deterministically using compiled regex patterns and heuristic rubrics without incurring API costs or latency ($< 2$ms per payload).
2. **Deterministic Anti-Hype Penalties:** Identify and penalize marketing buzzwords, hyperbolic claims, affiliate monetization patterns, and unsubstantiated guarantees.
3. **Credibility Offsets:** Recognize empirical research rigor (benchmarks, statistical validity, ablation studies, reproducible artifacts, open datasets, and high source authority).
4. **Immediate Drop Threshold:** Signals with a calculated `heuristic_noise_score > 0.60` must be dropped immediately with recorded audit reasons (`rejection_reasons`). Signals $\le 0.60$ qualify as `QualifiedSignal` for Stage 2 processing.
5. **Golden Benchmark Validation:** Must achieve $> 90\%$ precision on a regression benchmark containing verified empirical tools vs. hyperbolic vaporware.

## Options Considered

### Option 1: Rule-Based Compiled Heuristic Lexicon & Pattern Scorer (Selected)
- Implement regex-compiled matchers for:
  - **Hype & Superlatives:** "revolutionary", "game-changing", "100x faster", "miraculous", "silver bullet", "unprecedented".
  - **Unsubstantiated Absolutes:** "replaces all developers", "100% bug-free", "zero bugs guaranteed", "eliminates all testing".
  - **Commercial Spam & Listicles:** "promo code", "affiliate link", "top 10 tools you must buy", "click here to get 50% off".
- Implement offset credits for:
  - **Technical Rigor:** "empirical evaluation", "mutation score", "ablation study", "statistically significant", "controlled trial", "ground truth", "false positive rate".
  - **Source Authority:** Pre-prints ($W_{\text{auth}} = 1.3$) and enterprise blogs ($W_{\text{auth}} = 1.25$) receive baseline credibility dampening over unvetted community feeds.
- *Pros:* Instantaneous execution ($< 1$ms); 100% deterministic; zero LLM token spend; fully auditable.
- *Cons:* Requires maintaining the heuristic lexicon as new buzzwords emerge.

### Option 2: Lightweight Local SLM / Embedding Classifier (e.g., SetFit or DeBERTa)
- Train a small classification model to score hype vs rigor.
- *Pros:* Captures subtle semantic nuance.
- *Cons:* Adds heavy PyTorch/ONNX runtime dependencies; adds startup latency and hardware overhead in local environments.

## Decision Rationale
We adopt **Option 1**: A purely deterministic, rule-based `NoiseSieve` in `src/radar/pipeline/noise_sieve.py`.

### Mathematical Formulation
$$\text{Noise Score} = \text{clamp}\left( S_{\text{base}} + \sum w_{\text{hype}} - \sum w_{\text{cred}} - \Delta_{\text{auth}}, 0.0, 1.0 \right)$$
Where:
- $S_{\text{base}} = 0.20$ (baseline neutral noise)
- $\sum w_{\text{hype}}$: Cumulative penalty weights for matched hype/spam patterns ($+0.15$ to $+0.35$ per distinct indicator)
- $\sum w_{\text{cred}}$: Cumulative credibility credits for empirical indicators ($-0.10$ to $-0.25$)
- $\Delta_{\text{auth}} = (W_{\text{auth}} - 1.0) \times 0.20$: Source authority discount
- **Drop Gate:** If $\text{Noise Score} > 0.60 \implies \text{Drop}$; otherwise $\implies \text{Pass}$ to Stage 2.

## Consequences

### Positive
- Filters out ~40-60% of noisy raw signals prior to LLM evaluation, saving significant token spend.
- Millisecond-scale execution in memory.
- Clear explainability: every dropped signal logs exact pattern triggers.

### Negative / Trade-offs
- Highly novel marketing phrasing may occasionally pass through Stage 1, leaving final skepticism to Stage 3 Committee review.
