"""Stage 3 pgvector Topic Convergence and Parasitic Wrapper Detection Engine."""

import logging
import math
from collections.abc import Sequence
from uuid import UUID

from radar.core.config import settings
from radar.core.models import (
    ConvergenceResult,
    EvidenceTier,
    LifecycleStage,
    SignalDossier,
    SynthesizedTopic,
    TrendTopic,
)
from radar.providers.base import LLMProvider

logger = logging.getLogger(__name__)

DEFAULT_TOPIC_SYNTHESIS_SYSTEM_PROMPT = """You are a Principal AI Quality Engineering Architect and Technology Convergence Analyst.
Your task is to analyze a cluster of closely related technical dossiers and synthesize:
1. Canonical Name: A unified, professional name for this emerging trend/technique (e.g. 'Predictive Test Selection with Graph Neural Networks').
2. Summary: A 2-3 sentence technical summary capturing the core shared innovation, methodology, and practical engineering significance.
3. Primary Category: The consensus Quality Engineering domain pillar representing this cluster.

Be objective, precise, and avoid hype."""


def compute_cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute mathematical cosine similarity between two dense vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot = math.fsum(a * b for a, b in zip(vec_a, vec_b, strict=True))
    norm_a = math.sqrt(math.fsum(a * a for a in vec_a))
    norm_b = math.sqrt(math.fsum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    sim = dot / (norm_a * norm_b)
    return max(0.0, min(1.0, sim))


class TopicConvergenceEngine:
    """Stage 3 Topic Convergence and Parasitic Wrapper Detection Engine (Option 3B)."""

    def __init__(
        self,
        provider: LLMProvider,
        convergence_threshold: float = settings.topic_convergence_threshold,
        wrapper_threshold: float = settings.wrapper_similarity_threshold,
        wrapper_penalty: float = settings.wrapper_penalty,
        corroboration_bonus: float = settings.corroboration_consensus_bonus,
        system_prompt: str = DEFAULT_TOPIC_SYNTHESIS_SYSTEM_PROMPT,
    ) -> None:
        self.provider = provider
        self.convergence_threshold = convergence_threshold
        self.wrapper_threshold = wrapper_threshold
        self.wrapper_penalty = wrapper_penalty
        self.corroboration_bonus = corroboration_bonus
        self.system_prompt = system_prompt

        self._topics: dict[UUID, TrendTopic] = {}
        self._dossiers: dict[UUID, SignalDossier] = {}

    def get_topic(self, topic_id: UUID) -> TrendTopic | None:
        """Retrieve a trend topic by ID from local working memory."""
        return self._topics.get(topic_id)

    def get_all_topics(self) -> list[TrendTopic]:
        """Retrieve all active trend topics."""
        return list(self._topics.values())

    @staticmethod
    def _detect_channel(url: str) -> str:
        """Categorize source channel based on URL patterns."""
        lowered = url.lower()
        if "arxiv.org" in lowered:
            return "arxiv"
        elif "github.com" in lowered:
            return "github"
        else:
            return "practitioner"

    async def _synthesize_topic(self, dossiers: Sequence[SignalDossier]) -> SynthesizedTopic:
        """Synthesize a unified topic name and summary across cluster dossiers using the LLM provider."""
        lines = ["Convergent Technical Innovations:"]
        for d in dossiers:
            lines.append(
                f"- Name: {d.name} | Category: {d.category.value} | Tier: {d.evidence_tier.value}"
            )
            lines.append(f"  Key Innovation: {d.key_innovation}")
            if d.technical_claims:
                lines.append(f"  Claims: {'; '.join(d.technical_claims)}")

        prompt = "\n".join(lines)
        return await self.provider.generate_structured(
            prompt,
            SynthesizedTopic,
            self.system_prompt,
        )

    async def converge_dossier(self, dossier: SignalDossier) -> ConvergenceResult:
        """Cluster an incoming signal dossier into a TrendTopic and audit for parasitic wrappers."""
        if not dossier.embedding:
            # Cannot calculate similarity without embedding; seed independent topic
            synthesized = await self._synthesize_topic([dossier])
            topic = TrendTopic(
                name=synthesized.name,
                category=synthesized.primary_category,
                summary=synthesized.summary,
                corroboration_count=1,
                sources=[dossier.source_url],
                average_viability=0.5,
                average_validity=0.5,
                lifecycle_stage=LifecycleStage.EMERGING,
            )
            dossier.topic_id = topic.id
            self._topics[topic.id] = topic
            self._dossiers[dossier.id] = dossier
            return ConvergenceResult(
                dossier_id=dossier.id,
                topic_id=topic.id,
                is_new_topic=True,
                similarity_score=0.0,
                is_wrapper=False,
                wrapper_penalty_applied=0.0,
                multi_source_consensus=False,
                corroboration_count=1,
            )

        # Search for closest existing dossier across memory
        best_sim = 0.0
        best_match: SignalDossier | None = None

        for existing_id, existing in self._dossiers.items():
            if existing_id == dossier.id or not existing.embedding:
                continue
            sim = compute_cosine_similarity(dossier.embedding, existing.embedding)
            if sim > best_sim:
                best_sim = sim
                best_match = existing

        # Case A: Below convergence threshold -> Seed new topic
        if best_match is None or best_sim < self.convergence_threshold:
            synthesized = await self._synthesize_topic([dossier])
            topic = TrendTopic(
                name=synthesized.name,
                category=synthesized.primary_category,
                summary=synthesized.summary,
                corroboration_count=1,
                sources=[dossier.source_url],
                average_viability=0.5,
                average_validity=0.5,
                lifecycle_stage=LifecycleStage.EMERGING,
            )
            dossier.topic_id = topic.id
            self._topics[topic.id] = topic
            self._dossiers[dossier.id] = dossier

            return ConvergenceResult(
                dossier_id=dossier.id,
                topic_id=topic.id,
                is_new_topic=True,
                similarity_score=best_sim,
                is_wrapper=False,
                wrapper_penalty_applied=0.0,
                multi_source_consensus=False,
                corroboration_count=1,
            )

        # Case B: Converges into best_match cluster
        target_topic_id = best_match.topic_id
        if target_topic_id is None or target_topic_id not in self._topics:
            # Fallback in case target topic was not initialized
            synthesized = await self._synthesize_topic([best_match, dossier])
            topic = TrendTopic(
                name=synthesized.name,
                category=synthesized.primary_category,
                summary=synthesized.summary,
                corroboration_count=2,
                sources=[best_match.source_url, dossier.source_url],
                average_viability=0.5,
                average_validity=0.5,
                lifecycle_stage=LifecycleStage.EMERGING,
            )
            self._topics[topic.id] = topic
            best_match.topic_id = topic.id
            target_topic_id = topic.id
        else:
            topic = self._topics[target_topic_id]

        # Audit Parasitic Wrapper Condition
        is_wrapper = False
        penalty = 0.0
        if best_sim >= self.wrapper_threshold:
            if dossier.is_superficial_wrapper or (
                not dossier.has_reproducible_benchmark
                and not dossier.has_open_source_repo
                and dossier.evidence_tier != EvidenceTier.ENGINEERING_POST_MORTEM
            ):
                is_wrapper = True
                dossier.is_superficial_wrapper = True
                penalty = self.wrapper_penalty

        # Attach to topic
        dossier.topic_id = topic.id
        self._dossiers[dossier.id] = dossier

        # Find all dossiers in this topic
        cluster_dossiers = [d for d in self._dossiers.values() if d.topic_id == topic.id]

        # Assess multi-source consensus
        channels = {self._detect_channel(d.source_url) for d in cluster_dossiers}
        multi_source_consensus = len(channels) >= 3

        # Re-synthesize unified topic
        synthesized = await self._synthesize_topic(cluster_dossiers)
        topic.name = synthesized.name
        topic.summary = synthesized.summary
        topic.category = synthesized.primary_category
        topic.corroboration_count = len(cluster_dossiers)
        topic.sources = list({d.source_url for d in cluster_dossiers})

        # Calculate adjusted validity score
        adj_validity = topic.average_validity - penalty
        if multi_source_consensus:
            adj_validity += self.corroboration_bonus
        topic.average_validity = max(0.0, min(1.0, adj_validity))

        return ConvergenceResult(
            dossier_id=dossier.id,
            topic_id=topic.id,
            is_new_topic=False,
            similarity_score=best_sim,
            is_wrapper=is_wrapper,
            wrapper_penalty_applied=penalty,
            multi_source_consensus=multi_source_consensus,
            corroboration_count=topic.corroboration_count,
        )

    async def converge_batch(self, dossiers: Sequence[SignalDossier]) -> list[ConvergenceResult]:
        """Sequentially process a batch of dossiers into converged topics."""
        results: list[ConvergenceResult] = []
        for d in dossiers:
            res = await self.converge_dossier(d)
            results.append(res)
        return results
