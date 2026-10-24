"""Stage 3 Multi-Lens Evaluator Committee (Option 2C)."""

import asyncio
import logging
from collections.abc import Sequence
from uuid import UUID

from radar.core.config import settings
from radar.core.models import (
    CommitteeAuditResult,
    EnterpriseEvaluation,
    SignalDossier,
    TrendTopic,
)
from radar.providers.base import LLMProvider

logger = logging.getLogger(__name__)

DEFAULT_COMMITTEE_SYSTEM_PROMPT = """You are the Adversarial Enterprise Evaluation Committee for an executive Technology Horizon Radar.
Your mandate is to conduct a rigorous, skeptical audit of emerging AI test engineering tools and frameworks against Tier-1 enterprise banking and defense constraints.

Evaluate the innovation through three discrete adversarial lenses:

1. Enterprise Security & Privacy Lens (Weight: 35%):
   - Data Egress Boundaries: Does the tool require sending proprietary code, test fixtures, or system telemetry to third-party public LLM endpoints?
   - Air-Gap / VPC Compatibility: Can it operate purely within on-premise or air-gapped VPCs using local weights (e.g. vLLM / Ollama)?
   - Secret & Credential Handling: Does it properly mask credentials, database connection strings, and PII in test schemas?
   - Threat Vectors: Risks of prompt injection in test synthesis, model weight poisoning, or arbitrary code execution in test runners.

2. Enterprise DevOps & CI/CD Operations Lead (Weight: 35%):
   - Determinism & Flakiness: Are generated tests deterministic and replayable with fixed random seeds, or do they cause flaky PR gate failures?
   - Runner & Infrastructure Footprint: Does execution demand expensive multi-GPU clusters, or can it execute on lightweight ephemeral CI runners?
   - Pipeline Latency: Does it introduce unacceptable merge queue latency?
   - Maintenance & Brittleness: Are generated tests brittle to minor UI/DOM or refactoring changes?

3. Principal AI Quality Engineering Architect (Weight: 30%):
   - Real-World Defect Resolution: Does it expose complex semantic bugs, race conditions, and boundary conditions, or merely pass trivial syntactic vanity checks?
   - Empirical Rigor: Are claims substantiated on realistic industrial benchmarks vs contrived synthetic examples?
   - Behavioral Soundness: Does it verify formal invariant contracts or merely overfit existing legacy behavior?

Assign an objective score between 0.0 (unusable / critical blocker) and 1.0 (exemplary / enterprise-ready) for each lens.
Provide detailed adversarial critiques for each lens, list specific enterprise risks and adoption prerequisites, and synthesize an executive skeptic verdict."""


class MultiLensEvaluator:
    """Stage 3 Multi-Lens Adversarial Evaluation Committee."""

    def __init__(
        self,
        provider: LLMProvider,
        security_weight: float = settings.security_weight,
        cicd_weight: float = settings.cicd_weight,
        qe_weight: float = settings.qe_weight,
        system_prompt: str = DEFAULT_COMMITTEE_SYSTEM_PROMPT,
    ) -> None:
        self.provider = provider
        self.security_weight = security_weight
        self.cicd_weight = cicd_weight
        self.qe_weight = qe_weight
        self.system_prompt = system_prompt

    def _build_prompt(self, dossier: SignalDossier, topic: TrendTopic | None = None) -> str:
        """Construct the multi-perspective audit prompt."""
        lines = [
            f"Technology / Innovation Name: {dossier.name}",
            f"QE Category Pillar: {dossier.category.value}",
            f"Evidence Tier: {dossier.evidence_tier.value}",
            f"Source URL: {dossier.source_url}",
            f"Key Innovation: {dossier.key_innovation}",
        ]

        if topic is not None:
            lines.append(
                f"Converged Trend Topic: {topic.name} (Corroborations: {topic.corroboration_count})"
            )
            lines.append(f"Topic Summary: {topic.summary}")

        if dossier.technical_claims:
            lines.append("Technical Claims:")
            for c in dossier.technical_claims:
                lines.append(f"  - {c}")

        lines.append(
            f"Artifact Indicators: Reproducible Benchmark={dossier.has_reproducible_benchmark}, Open Source Repo={dossier.has_open_source_repo}, Superficial Wrapper={dossier.is_superficial_wrapper}"
        )

        lines.append("")
        lines.append(
            "Perform a rigorous adversarial evaluation across Security (35%), Operations/CI-CD (35%), and Technical Rigor (30%). "
            "Return scores (0.0 to 1.0), specific critiques, enterprise risks, prerequisites, and a skeptic verdict."
        )
        return "\n".join(lines)

    async def evaluate(
        self, dossier: SignalDossier, topic: TrendTopic | None = None
    ) -> EnterpriseEvaluation:
        """Conduct an adversarial multi-lens evaluation of a signal dossier."""
        prompt = self._build_prompt(dossier, topic)

        audit: CommitteeAuditResult = await self.provider.generate_structured(
            prompt,
            CommitteeAuditResult,
            self.system_prompt,
        )

        composite_viability = round(
            self.security_weight * audit.security_score
            + self.cicd_weight * audit.cicd_score
            + self.qe_weight * audit.qe_score,
            4,
        )
        clamped_viability = max(0.0, min(1.0, composite_viability))

        return EnterpriseEvaluation(
            dossier_id=dossier.id,
            security_score=audit.security_score,
            cicd_score=audit.cicd_score,
            qe_score=audit.qe_score,
            composite_viability_score=clamped_viability,
            enterprise_risks=audit.enterprise_risks,
            prerequisites=audit.prerequisites,
            security_critique=audit.security_critique,
            cicd_critique=audit.cicd_critique,
            qe_critique=audit.qe_critique,
            skeptic_critique=audit.skeptic_critique,
        )

    async def evaluate_batch(
        self,
        dossiers: Sequence[SignalDossier],
        topics: dict[UUID, TrendTopic] | None = None,
    ) -> list[EnterpriseEvaluation]:
        """Concurrently evaluate a batch of signal dossiers."""
        tasks = [
            self.evaluate(
                d,
                topics.get(d.topic_id) if (topics and d.topic_id) else None,
            )
            for d in dossiers
        ]
        return list(await asyncio.gather(*tasks))
