"""Stage 4 Radar Categorizer and Lifecycle Trajectory Engine."""

import logging
from collections.abc import Sequence
from uuid import UUID

from radar.core.config import settings
from radar.core.models import (
    EnterpriseEvaluation,
    EvidenceTier,
    LifecycleStage,
    RadarItem,
    RadarRing,
    SignalDossier,
    TrendTopic,
)

logger = logging.getLogger(__name__)


class RadarCategorizer:
    """Stage 4 Categorizer computing validity, hype, Tech Radar ring, and lifecycle trajectory."""

    def __init__(
        self,
        adopt_min_viability: float = settings.ring_adopt_min_viability,
        adopt_max_hype: float = settings.ring_adopt_max_hype,
        trial_min_viability: float = settings.ring_trial_min_viability,
        trial_max_hype: float = settings.ring_trial_max_hype,
        assess_min_viability: float = settings.ring_assess_min_viability,
        velocity_emerging: float = settings.velocity_emerging_threshold,
        velocity_fading: float = settings.velocity_fading_threshold,
    ) -> None:
        self.adopt_min_viability = adopt_min_viability
        self.adopt_max_hype = adopt_max_hype
        self.trial_min_viability = trial_min_viability
        self.trial_max_hype = trial_max_hype
        self.assess_min_viability = assess_min_viability
        self.velocity_emerging = velocity_emerging
        self.velocity_fading = velocity_fading

    def calculate_validity_and_hype(
        self, dossier: SignalDossier, topic: TrendTopic | None = None
    ) -> tuple[float, float]:
        """Compute signal validity score (S_v) and derived hype score (H = 1.0 - S_v)."""
        validity = 0.50

        # Anti-hype deductions
        if (
            not dossier.has_reproducible_benchmark
            and not dossier.has_open_source_repo
            and dossier.evidence_tier != EvidenceTier.ENGINEERING_POST_MORTEM
        ):
            validity -= 0.30
        if dossier.is_superficial_wrapper:
            validity -= 0.20
        if dossier.evidence_tier == EvidenceTier.VENDOR_ANNOUNCEMENT:
            validity -= 0.15

        # Engineering & convergence bonuses
        if (
            dossier.evidence_tier == EvidenceTier.ACADEMIC_PEER_REVIEWED
            and dossier.has_reproducible_benchmark
        ):
            validity += 0.30
        if topic is not None and topic.corroboration_count >= 3:
            validity += 0.25
        velocity = dossier.engagement_metrics.get("velocity", 0.0)
        if velocity >= self.velocity_emerging:
            validity += 0.20
        if dossier.evidence_tier == EvidenceTier.ENGINEERING_POST_MORTEM:
            validity += 0.20

        clamped_validity = round(max(0.0, min(1.0, validity)), 4)
        hype = round(max(0.0, min(1.0, 1.0 - clamped_validity)), 4)
        return clamped_validity, hype

    def determine_ring(self, viability: float, hype: float, dossier: SignalDossier) -> RadarRing:
        """Assign Tech Radar ring based on multi-lens viability, hype, and artifact backing."""
        if dossier.is_superficial_wrapper or viability < self.assess_min_viability or hype > 0.60:
            return RadarRing.HOLD

        has_proven_backing = (
            dossier.has_reproducible_benchmark
            or dossier.has_open_source_repo
            or dossier.evidence_tier == EvidenceTier.ENGINEERING_POST_MORTEM
        )
        if (
            viability >= self.adopt_min_viability
            and hype <= self.adopt_max_hype
            and has_proven_backing
        ):
            return RadarRing.ADOPT

        if viability >= self.trial_min_viability and hype <= self.trial_max_hype:
            return RadarRing.TRIAL

        if (
            viability >= self.assess_min_viability
            or dossier.engagement_metrics.get("velocity", 0.0) >= self.velocity_emerging
        ):
            return RadarRing.ASSESS

        return RadarRing.HOLD

    def determine_lifecycle(
        self, dossier: SignalDossier, topic: TrendTopic | None = None
    ) -> LifecycleStage:
        """Classify lifecycle trajectory from velocity and cross-channel corroboration."""
        corroboration = topic.corroboration_count if topic else 1
        velocity = dossier.engagement_metrics.get("velocity", 0.0)

        if corroboration >= 3:
            return LifecycleStage.CONSOLIDATED

        if velocity >= self.velocity_emerging:
            return LifecycleStage.EMERGING

        if velocity < self.velocity_fading:
            return LifecycleStage.FADING

        # Middle velocity range (5.0 to 25.0)
        if dossier.has_open_source_repo or dossier.has_reproducible_benchmark:
            return LifecycleStage.CONSOLIDATED

        return LifecycleStage.EMERGING

    def categorize(
        self,
        dossier: SignalDossier,
        evaluation: EnterpriseEvaluation,
        topic: TrendTopic | None = None,
    ) -> RadarItem:
        """Synthesize dossier, evaluation, and topic into a published RadarItem."""
        validity, hype = self.calculate_validity_and_hype(dossier, topic)
        ring = self.determine_ring(evaluation.composite_viability_score, hype, dossier)
        trajectory = self.determine_lifecycle(dossier, topic)

        sources = topic.sources if topic else [dossier.source_url]
        corroboration_count = topic.corroboration_count if topic else 1

        return RadarItem(
            dossier_id=dossier.id,
            evaluation_id=evaluation.id,
            topic_id=topic.id if topic else None,
            name=dossier.name,
            category=dossier.category,
            source_url=dossier.source_url,
            evidence_tier=dossier.evidence_tier,
            hype_score=hype,
            viability_score=evaluation.composite_viability_score,
            validity_score=validity,
            recommended_ring=ring,
            lifecycle_stage=trajectory,
            corroboration_count=corroboration_count,
            velocity_score=dossier.engagement_metrics.get("velocity", 0.0),
            corroborating_sources=sources,
            key_innovation=dossier.key_innovation,
            enterprise_risks=evaluation.enterprise_risks,
            prerequisites=evaluation.prerequisites,
            active=True,
        )

    def categorize_batch(
        self,
        dossiers: Sequence[SignalDossier],
        evaluations: Sequence[EnterpriseEvaluation],
        topics: dict[UUID, TrendTopic] | None = None,
    ) -> list[RadarItem]:
        """Synthesize batches of dossiers and evaluations into RadarItems."""
        eval_map = {e.dossier_id: e for e in evaluations}
        items: list[RadarItem] = []

        for d in dossiers:
            if d.id in eval_map:
                topic = topics.get(d.topic_id) if (topics and d.topic_id) else None
                item = self.categorize(d, eval_map[d.id], topic)
                items.append(item)

        return items
