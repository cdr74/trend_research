# ADR 0011: Stage 2 Deep Extractor Agent with Schema Validation and Vector Embeddings

## Status
Accepted

## Context
In the 4-stage processing DAG established in ADR-0000 and ADR-0004, Stage 2 (Deep Extractor) bridges raw, filtered source content (`QualifiedSignal`) and structured architectural evaluation. Signals passing Stage 1 have been stripped of marketing spam and hyperbolic noise, but remain unstructured text (paper abstracts, repository READMEs, technical blog articles).

Stage 2 must transform this unstructured content into a strictly typed, auditable `SignalDossier`:
1. **Tool / Technology Name:** Clean canonical entity name.
2. **QE Domain Pillar Classification:** Exactly one of the 6 Quality Engineering pillars (`Spec & Model`, `Test Synthesis`, `Execution & Optimization`, `Triage & Self-Healing`, `Agent Systems`, `Governance & Evals`).
3. **Evidence Tier:** Factual classification of backing evidence (`Academic Peer-Reviewed`, `Open Source Repo`, `Engineering Post-Mortem`, `Vendor Announcement`).
4. **Key Innovation:** Concise 1-2 sentence statement summarizing the fundamental technical advance.
5. **Concrete Technical Claims:** 2 to 5 verifiable, testable assertions made by the authors/creators.
6. **Artifact Indicators:** Explicit booleans for `has_reproducible_benchmark`, `has_open_source_repo`, and `is_superficial_wrapper`.
7. **Dense Semantic Embedding:** 1536-dimensional vector embedding derived from the extracted technical essence, enabling semantic topic clustering (`pgvector`) in Stage 3.

## Requirements & Constraints
1. **Decoupled LLM Extraction Schema:** Separate the LLM reasoning schema (`ExtractedInnovation`) from the persistence dossier (`SignalDossier`) to prevent model hallucination of internal database UUIDs or timestamps.
2. **Provider Agnosticism:** Must execute seamlessly via the `LLMProvider` interface across `AgyCliProvider` (local WSL), `OpenAICompatProvider` (Ollama/vLLM), `GeminiProvider`, and `MockProvider`.
3. **Embedding Text Synthesis:** Embeddings must not be computed over noisy raw HTML or boilerplate, but over a synthesized technical summary string: `"{name}: {key_innovation} {' '.join(technical_claims)}"`.
4. **Resilient Failure Handling:** Malformed extractions must trigger corrective re-prompting (handled at the provider level) or log graceful errors without aborting batch DAG processing.
5. **Hermetic Offline Testing:** Unit and pipeline integration tests must run without network access or paid API keys using `MockProvider`.

## Options Considered

### Option 1: Multi-Step LLM Chain (Classification -> Extraction -> Claim Verification)
- Run 3 separate prompt turns for category classification, claim extraction, and artifact verification.
- *Pros:* High specialization per turn.
- *Cons:* 3x token cost, 3x latency, complex state tracking; unnecessary given structured output capabilities of frontier models.

### Option 2: Single-Turn Pydantic Schema Extraction with Dedicated Vectorization (Selected)
- Execute a single comprehensive extraction prompt enforcing `ExtractedInnovation` Pydantic schema.
- Follow up with an asynchronous vector embedding call over the synthesized technical essence.
- Assemble the immutable `SignalDossier` carrying source references and engagement telemetry.
- *Pros:* Single LLM turn minimizes cost and latency; strict type safety; clear separation of concerns.
- *Cons:* Requires a rich, well-instructed system prompt explaining domain categories and evidence rubrics.

## Decision Rationale
We adopt **Option 2**. The `DeepExtractor` is implemented in `src/radar/pipeline/extractor.py`.

Key Design Specifications:
1. **Extraction Contract (`ExtractedInnovation`):**
   - Strictly typed with Pydantic v2 enums (`QECategory`, `EvidenceTier`).
   - Validated at runtime by the pluggable LLM provider adapter.
2. **System Instruction Prompt:**
   - Detailed definitions of the 6 Quality Engineering pillars to ensure consistent categorization.
   - Guidelines for detecting superficial wrappers (e.g., repackaging standard LLMs without novel architecture or datasets).
3. **Embedding Vectorization:**
   - Calls `provider.embed_text()` to generate 1536-dimensional vectors for PostgreSQL `pgvector` indexing.
4. **Integration with Persistence:**
   - Extracted dossiers can be persisted to the `signal_dossiers` table using `RadarRepository.save_dossier()`.

## Consequences

### Positive
- High-fidelity structured fact extraction with zero schema drift.
- Uniform execution across local `agy`, cloud Gemini, and local Ollama/vLLM.
- Seamless compatibility with `pgvector` topic convergence in Stage 3.
- Fast, reproducible testing via `MockProvider`.

### Negative / Trade-offs
- Highly ambiguous hybrid tools (e.g., tools spanning both "Test Synthesis" and "Agent Systems") require prompt guidelines to prioritize primary architectural contribution.
