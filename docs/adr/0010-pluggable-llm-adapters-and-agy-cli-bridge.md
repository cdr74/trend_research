# ADR 0010: Pluggable LLM Adapters with Local Antigravity (`agy`) CLI Bridge

## Status
Accepted

## Context
Milestone 3 (Task `M3-T1`) requires integrating Large Language Models into the radar for Stage 2 (Deep Extractor) and Stage 3 (Adversarial Multi-Lens Committee). In an enterprise development environment running on WSL (Windows Subsystem for Linux), relying solely on metered commercial cloud API keys for high-volume developer experimentation creates recurring token costs. Conversely, running large local open-weights reasoning models (e.g., 70B+) locally requires dedicated GPU VRAM that may not always be available.

The developer environment already has the Antigravity CLI (`agy` version 1.4.7+) authenticated and available in the system PATH. The CLI supports non-interactive execution via `agy -p` (print mode) with native `--json-schema` enforcement and `--output-format json`.

The architecture requires an adapter ecosystem that seamlessly switches between:
1. **Local Antigravity CLI Bridge (`AgyCliProvider`):** Non-interactive local execution invoking `agy -p` with strict JSON schema enforcement, leveraging the developer's active workspace session at zero incremental API cost.
2. **OpenAI-Compatible REST Provider (`OpenAICompatProvider`):** Supporting self-hosted Ollama, vLLM, and OpenAI endpoints via asynchronous HTTP.
3. **Google Gemini REST Provider (`GeminiProvider`):** Supporting Google Gemini models via async REST endpoints.
4. **Deterministic Mock Provider (`MockProvider`):** Zero-latency synthetic generator for hermetic CI pipelines and unit tests.

## Requirements & Constraints
1. **Unified Interface Contract:** All providers must adhere to the `LLMProvider` protocol:
   - `generate_text(prompt, system_prompt) -> str`
   - `generate_structured(prompt, response_model: Type[T], system_prompt) -> T`
   - `embed_text(text) -> list[float]`
2. **Schema-Enforced Structured Generation:** Structured outputs must strictly validate against Pydantic v2 models. For the `agy` bridge, the model's JSON schema (`response_model.model_json_schema()`) is passed via `--json-schema`, and the returned `structured_output` is parsed directly into the target Pydantic class.
3. **Resilient JSON Recovery:** For models returning markdown fences (e.g. ````json ... ````), the parser must extract the inner payload and attempt validation, falling back to a single corrective re-prompt if validation fails.
4. **Asynchronous Non-Blocking Execution:** Subprocess calls (`agy`) and network calls (`httpx`) must execute asynchronously using `asyncio.create_subprocess_exec` and `httpx.AsyncClient` without blocking the pipeline DAG event loop.
5. **Zero External SDK Drift:** Network providers must use standard `httpx.AsyncClient` rather than requiring bulky proprietary SDKs as mandatory dependencies.

## Options Considered

### Option 1: REST-Only Remote Providers
- Only support Gemini API and OpenAI/Ollama endpoints over HTTP.
- *Pros:* Standard server deployment model.
- *Cons:* Incurs API costs on commercial endpoints and cannot leverage the local authenticated `agy` session available on WSL.

### Option 2: Heavyweight Agent Frameworks (LangChain, LiteLLM)
- Wrap calls using an external multi-provider framework.
- *Pros:* Broad provider catalogs.
- *Cons:* Dependency bloat, breaking version changes, opaque error states, and no native support for the `agy` CLI bridge.

### Option 3: Pluggable Adapter Architecture with `agy` CLI Bridge (Selected)
- Implement `AgyCliProvider`, `OpenAICompatProvider`, `GeminiProvider`, and `MockProvider` behind a unified protocol.
- *Pros:* Perfect cost efficiency on WSL via `agy`; seamless fallback to Ollama/vLLM or Gemini in headless server environments; fully testable via mocks; zero extra dependencies.
- *Cons:* Subprocess execution overhead (~1-2 seconds per invocation) compared to a persistent in-process HTTP connection.

## Decision Rationale
We adopt **Option 3**. The provider selection is controlled via `RADAR_LLM_PROVIDER` in `Settings`:
- `RADAR_LLM_PROVIDER=agy` (default on developer WSL environments)
- `RADAR_LLM_PROVIDER=openai_compat` (for local Ollama or server vLLM)
- `RADAR_LLM_PROVIDER=gemini` (for cloud Gemini)
- `RADAR_LLM_PROVIDER=mock` (for tests and CI runs)

For embeddings, `RADAR_EMBEDDING_PROVIDER` defaults to `mock` or `openai_compat` (e.g., Ollama `nomic-embed-text`) when running with `agy`.

## Consequences

### Positive
- Zero incremental token cost for local developer evaluations on WSL via `agy`.
- Complete flexibility to deploy the same pipeline to remote servers using Ollama, vLLM, or cloud APIs.
- Strict Pydantic v2 runtime validation on all extraction and committee outputs.
- 100% test coverage using offline subprocess and HTTP mocks.

### Negative / Trade-offs
- The `AgyCliProvider` requires `agy` installed and logged in on the host system. If not found, a clear `ProviderError` must guide the user to configure `agy` or switch to `mock`/`openai_compat`.
