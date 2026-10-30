"""Stage 4 Radar Categorizer and Lifecycle Trajectory Engine."""

import logging
from collections.abc import Sequence
from typing import Any
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
        stars_consolidated_threshold: float = settings.stars_consolidated_threshold,
        max_exemplars_per_topic: int = settings.max_exemplars_per_topic,
    ) -> None:
        self.adopt_min_viability = adopt_min_viability
        self.adopt_max_hype = adopt_max_hype
        self.trial_min_viability = trial_min_viability
        self.trial_max_hype = trial_max_hype
        self.assess_min_viability = assess_min_viability
        self.velocity_emerging = velocity_emerging
        self.velocity_fading = velocity_fading
        self.stars_consolidated = stars_consolidated_threshold
        self.max_exemplars_per_topic = max_exemplars_per_topic

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

    def determine_ring(
        self,
        viability: float,
        hype: float,
        dossier: SignalDossier,
        lifecycle_stage: LifecycleStage = LifecycleStage.EMERGING,
    ) -> RadarRing:
        """Assign Tech Radar ring based on multi-lens viability, hype, lifecycle stage, and artifact backing."""
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
            and lifecycle_stage == LifecycleStage.CONSOLIDATED
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
        """Classify lifecycle trajectory from velocity, star count, and cross-channel corroboration."""
        corroboration = topic.corroboration_count if topic else 1
        velocity = dossier.engagement_metrics.get("velocity", 0.0)
        stars = dossier.engagement_metrics.get("stars", 0.0)

        if corroboration >= 3 or stars >= self.stars_consolidated:
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
        trajectory = self.determine_lifecycle(dossier, topic)
        ring = self.determine_ring(
            evaluation.composite_viability_score,
            hype,
            dossier,
            lifecycle_stage=trajectory,
        )

        sources = topic.sources if topic else [dossier.source_url]
        corroboration_count = topic.corroboration_count if topic else 1
        category = topic.category if topic else dossier.category

        return RadarItem(
            dossier_id=dossier.id,
            evaluation_id=evaluation.id,
            topic_id=topic.id if topic else None,
            topic_name=topic.name if topic else None,
            name=dossier.name,
            track=dossier.track,
            category=category,
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
            is_canonical=True,
        )

    @staticmethod
    def _extract_namespace(item: Any) -> str:
        """Extract owner or organization namespace from repository URL or entity name."""
        url = str(getattr(item, "source_url", "")).lower()
        if "github.com/" in url:
            parts = url.split("github.com/")[-1].split("/")
            if len(parts) >= 2:
                return parts[0]
        name = str(getattr(item, "name", "")).lower()
        if "/" in name:
            return name.split("/")[0].strip()
        return name

    def consolidate_canonical_exemplars(
        self, items: Sequence[Any], max_exemplars_per_topic: int | None = None
    ) -> list[Any]:
        """Elect canonical exemplars per topic cluster and roll long-tail evidence into corroborating sources (ADR-0028)."""
        limit = max_exemplars_per_topic or self.max_exemplars_per_topic
        if not items:
            return []

        # Group items by topic (id or name)
        grouped: dict[str, list[Any]] = {}
        for it in items:
            topic_id = getattr(it, "topic_id", None)
            topic_name = getattr(it, "topic_name", None)
            key = str(topic_id) if topic_id else (topic_name or "Independent Innovation")
            grouped.setdefault(key, []).append(it)

        ring_weights: dict[Any, float] = {
            RadarRing.ADOPT: 1.0,
            RadarRing.TRIAL: 0.75,
            RadarRing.ASSESS: 0.50,
            RadarRing.HOLD: 0.25,
            "Adopt": 1.0,
            "Trial": 0.75,
            "Assess": 0.50,
            "Hold": 0.25,
        }

        output: list[Any] = []

        for _topic_key, topic_items in grouped.items():
            if len(topic_items) <= limit:
                for it in topic_items:
                    it.is_canonical = True
                    output.append(it)
                continue

            # Compute exemplar composite score for each item
            def _score_item(it: Any, selected_namespaces: set[str]) -> float:
                ring_val = getattr(it, "recommended_ring", RadarRing.HOLD)
                ring_wt = ring_weights.get(ring_val, 0.25)
                viab = float(getattr(it, "viability_score", 0.0))
                vel = float(getattr(it, "velocity_score", 0.0))
                vel_norm = min(1.0, vel / 100.0)
                base_score = (ring_wt * 0.40) + (viab * 0.35) + (vel_norm * 0.25)
                ns = self._extract_namespace(it)
                # Apply diversity penalty if namespace already has an elected exemplar
                if ns in selected_namespaces:
                    base_score -= 0.30
                return base_score

            # Iteratively select top K diverse exemplars
            candidates = list(topic_items)
            canonical_exemplars: list[Any] = []
            selected_namespaces: set[str] = set()

            for _ in range(limit):
                if not candidates:
                    break
                best_item = max(candidates, key=lambda it: _score_item(it, selected_namespaces))
                candidates.remove(best_item)
                canonical_exemplars.append(best_item)
                selected_namespaces.add(self._extract_namespace(best_item))

            non_canonical_items = candidates

            # Gather corroborating evidence from non-canonical cluster members
            additional_sources: list[str] = []
            for nci in non_canonical_items:
                s_url = getattr(nci, "source_url", "")
                if s_url and s_url not in additional_sources:
                    additional_sources.append(s_url)

            # Mark canonical items and roll up corroborating sources
            for cit in canonical_exemplars:
                cit.is_canonical = True
                existing_sources = list(getattr(cit, "corroborating_sources", []))
                for s in additional_sources:
                    if s not in existing_sources:
                        existing_sources.append(s)
                cit.corroborating_sources = existing_sources
                curr_count = int(getattr(cit, "corroboration_count", 1))
                cit.corroboration_count = max(curr_count, len(existing_sources))
                output.append(cit)

            # Mark non-canonical items
            for nci in non_canonical_items:
                nci.is_canonical = False
                output.append(nci)

        return output

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

        return self.consolidate_canonical_exemplars(items)
