# ADR 0016: Executive Markdown Intelligence Digest Generator

## Status
Accepted

## Context
While the Trend Horizon Radar provides CLI query capabilities (`radar query`) and a decoupled D3 web dashboard (`web/`), engineering leaders and enterprise architects require portable, version-controllable intelligence briefings. Periodic executive digests must summarize findings in an auditable, static document that can be reviewed in pull requests, published to wikis, or archived in the repository (`reports/`).

## Requirements & Constraints
1. **Comprehensive Executive Structure:**
   - **Executive Summary:** Macro-level trends and ring item counts.
   - **Tech Radar Ring Breakdown:** Tabular overview of `Adopt`, `Trial`, `Assess`, and `Hold` items with validity, viability, and hype scores.
   - **Converged Technology Clusters:** Key `TrendTopic`s with multi-source corroboration counts and source URLs.
   - **Deep Technical Spotlights:** High-priority items highlighting key technical claims, evidence tiers, and architectural prerequisites.
   - **Adversarial Committee Risk Radar:** Aggregated enterprise security and CI/CD determinism risks.
   - **Wrapper Quarantine Log:** Explicit disclosure of superficial wrappers and hype deductions.
   - **Audience Velocity Movers:** Fast-moving emerging tools vs. fading technologies.
2. **Deterministic Markdown Formatting:**
   - Clean, GitHub Flavored Markdown (GFM) tables, alerts, and structured headers.
   - Deterministic sorting by ring priority (`Adopt` -> `Trial` -> `Assess` -> `Hold`) and viability score.
3. **CLI Operations:**
   - Invoked via `radar report --output <PATH> [--mock]`.
4. **Offline & Database Safety:**
   - When the database is offline or unreachable, `radar report` halts with an informative error and does not emit an incomplete or empty report, unless `--mock` is explicitly passed for offline test verification.

## Options Considered

### Option 1: LLM-Generated Dynamic Report Free-Text
- Feed database JSON to an LLM provider to write an unconstrained essay report.
- *Pros:* Conversational phrasing.
- *Cons:* High token cost, hallucination risk, inconsistent sections, non-deterministic formatting; prone to omitting critical risk flags.

### Option 2: Deterministic Structured Markdown Generator (Selected)
- Implement a dedicated report generator in `src/radar/presentation/report.py` assembling audited entities directly into structured Markdown templates with calculated totals, formatted tables, and exact skeptic critiques.
- *Pros:* 100% deterministic, zero token cost, complete audit fidelity, instantaneous generation.
- *Cons:* Fixed structural sections; mitigated by modular design.

## Decision Rationale
We adopt **Option 2**. The `MarkdownReportGenerator` is implemented in `src/radar/presentation/report.py`.

## Consequences
### Positive
- Instantaneous, zero-cost intelligence reporting.
- High-fidelity synchronization between database state and published digests.
- Portable Markdown artifacts compatible with Git-based review workflows.
- Safe offline behavior preventing corrupted or empty report generation.

### Negative / Trade-offs
- Template layout requires code changes to alter section ordering or table columns.
