# ADR 0003: Pluggable LLM Provider Adapter Architecture

## Status
Accepted

## Context
Stages 2 and 3 of the AI Test Engineering Horizon Radar (Deep Extractor and Enterprise Skeptic) depend on LLMs to extract technical facts, analyze claims, and conduct adversarial banking-grade viability reviews.
In high-governance financial enterprise environments, the system must satisfy contrasting operational needs:
1. Cloud-based advanced reasoning models (e.g., Google Gemini 1.5 Pro / Flash, OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet) for rich extraction and multi-perspective critique.
2. Air-gapped / VPC-constrained local execution (e.g., Ollama, vLLM running open-weights models like Llama 3 or Mistral) for environments where proprietary code or internal test patterns must not leave the perimeter.
3. Deterministic structured output adherence (Pydantic models / JSON schemas) regardless of backend provider.

## Options Considered
1. **Custom Protocol / Pluggable Adapter Pattern (Selected)**:
   - Define a clean abstract interface `LLMProvider` with standard asynchronous methods: `generate_text()`, `generate_structured(schema: Type[BaseModel])`, and `embed_text()`.
   - Implement lightweight provider adapters: `GeminiProvider`, `OpenAICompatibleProvider` (covers OpenAI, Ollama, vLLM, Azure OpenAI), and `AnthropicProvider`.
   - Zero hard vendor lock-in; swapping models is an environment configuration change (`LLM_PROVIDER=gemini` or `LLM_PROVIDER=ollama`).
2. **Heavyweight Orchestration Frameworks (e.g. LangChain, LlamaIndex)**:
   - High dependency bloat, frequent breaking API changes, and unnecessary complexity for a deterministic 4-stage pipeline.
3. **Single Vendor SDK (e.g. only google-genai or openai)**:
   - Violates the enterprise neutrality requirement and prevents zero-egress local execution via Ollama/vLLM.

## Decision Rationale
We implement a **Pluggable LLM Adapter Architecture** using Python `typing.Protocol` / ABC:
- Native support for structured JSON generation enforcing strict Pydantic v2 schemas.
- Provider selection driven by configuration (`RADAR_LLM_PROVIDER`, `RADAR_EMBEDDING_PROVIDER`).
- Support for offline mock providers to allow deterministic, free unit testing without API keys or network latency.

## Consequences
### Positive
- Air-gapped banking compliance out of the box (works with local vLLM / Ollama endpoints).
- Fast, mockable test suite for CI pipelines without external network dependencies or token consumption.
- Extensible to future frontier models without altering pipeline DAG logic.

### Negative / Trade-offs
- Adapter layer must maintain compatibility across varying provider capabilities (e.g. prompt tuning or temperature adjustments when falling back to smaller local models).
