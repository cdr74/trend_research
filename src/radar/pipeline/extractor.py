"""Stage 2 Deep Extractor Agent: extracts structured technical innovation dossiers."""

import asyncio
import logging
from collections.abc import Sequence

from radar.core.models import (
    ExtractedInnovation,
    QualifiedSignal,
    SignalDossier,
    SourcePayload,
)
from radar.providers.base import LLMProvider

logger = logging.getLogger(__name__)

DEFAULT_EXTRACTOR_SYSTEM_PROMPT = """You are a Principal AI Quality Engineering Architect and Technical Intelligence Analyst.
Your mission is to perform deep fact extraction on technology pre-prints, repository codebases, and practitioner articles.
You must extract objective, verified technical facts and classify the innovation into the canonical Quality Engineering taxonomy.

Quality Engineering (QE) Domain Pillars:
- spec_and_model: Requirements formalization, domain-driven modeling, formal specifications, behavioral synthesis.
- test_synthesis: Automated test case generation, unit/integration/e2e test synthesis, property-based testing, fuzzing, mutation generation.
- execution_and_optimization: Test runners, parallel orchestration, mutation testing optimization, flaky test detection, test impact analysis, test suite minimization.
- triage_and_self_healing: Automated root cause analysis, bug localization, test self-healing, crash reproduction, repair suggestions.
- agent_systems: Multi-agent collaboration for QE, autonomous testing workflows, agentic code exploration and verification, tool-use agents.
- governance_and_evals: Evaluation harnesses, benchmark generation, LLM alignment evaluation, safety testing, compliance checking, quality metrics dashboards.

Evidence Tiers:
- academic_peer_reviewed: Rigorous academic paper with formal methodology or peer-reviewed publication (e.g. arXiv cs.SE with empirical studies).
- open_source_repo: Publicly accessible source repository with code, commit history, and automated test suite.
- engineering_post_mortem: Detailed real-world engineering blog post, architecture post-mortem, or production retrospective from known engineering teams.
- vendor_announcement: Commercial product launch, marketing announcement, or sponsored feature preview.

Wrapper & Artifact Detection:
- has_reproducible_benchmark: true if an empirical benchmark, public dataset, or replication package is explicitly cited or provided.
- has_open_source_repo: true if a link to an open-source code repository (GitHub, GitLab) is present.
- is_superficial_wrapper: true if the tool merely prompts a third-party commercial LLM without novel algorithmic pipelines, fine-tuned weights, agent loops, or execution infrastructure.

Be objective, concise, and rigorous. Extract 2 to 5 verifiable, falsifiable technical claims."""


class DeepExtractor:
    """Stage 2 Deep Extractor Agent transforming signals into structured SignalDossiers."""

    def __init__(
        self,
        provider: LLMProvider,
        system_prompt: str = DEFAULT_EXTRACTOR_SYSTEM_PROMPT,
    ) -> None:
        self.provider = provider
        self.system_prompt = system_prompt

    def _build_prompt(self, payload: SourcePayload) -> str:
        """Construct a structured extraction prompt from an ingested payload."""
        lines = [
            f"Source Channel: {payload.source_type.value}",
            f"Title: {payload.title}",
            f"Source URL: {payload.source_url}",
        ]
        if payload.author:
            lines.append(f"Author / Organization: {payload.author}")
        if payload.metadata:
            meta_str = ", ".join(f"{k}: {v}" for k, v in payload.metadata.items())
            lines.append(f"Metadata: {meta_str}")
        lines.append("")
        lines.append("Content Body / Abstract:")
        lines.append(payload.raw_content)
        lines.append("")
        lines.append(
            "Extract the canonical technology name, primary QE category, evidence tier, key innovation, "
            "concrete technical claims, and artifact verification flags conforming strictly to the requested schema."
        )
        return "\n".join(lines)

    async def extract(self, signal: QualifiedSignal | SourcePayload) -> SignalDossier:
        """Extract structured innovation dossier and dense vector embedding for a signal."""
        payload = signal.payload if isinstance(signal, QualifiedSignal) else signal

        prompt = self._build_prompt(payload)
        extracted: ExtractedInnovation = await self.provider.generate_structured(
            prompt,
            ExtractedInnovation,
            self.system_prompt,
        )

        # Synthesize dense semantic text representation for vector embedding
        embedding_text = (
            f"{extracted.name}: {extracted.key_innovation} {' '.join(extracted.technical_claims)}"
        )
        embedding = await self.provider.embed_text(embedding_text)

        return SignalDossier(
            source_id=payload.id,
            name=extracted.name,
            category=extracted.category,
            source_url=payload.source_url,
            evidence_tier=extracted.evidence_tier,
            key_innovation=extracted.key_innovation,
            technical_claims=extracted.technical_claims,
            has_reproducible_benchmark=extracted.has_reproducible_benchmark,
            has_open_source_repo=extracted.has_open_source_repo,
            is_superficial_wrapper=extracted.is_superficial_wrapper,
            embedding=embedding,
            engagement_metrics=payload.engagement_metrics,
        )

    async def extract_batch(
        self, signals: Sequence[QualifiedSignal | SourcePayload]
    ) -> list[SignalDossier]:
        """Extract dossiers across a batch of signals concurrently."""
        tasks = [self.extract(s) for s in signals]
        return list(await asyncio.gather(*tasks))
