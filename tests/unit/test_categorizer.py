"""Unit tests for the Stage 4 Radar Categorizer and Lifecycle Trajectory."""

from uuid import uuid4

import pytest

from radar.core.models import (
    EnterpriseEvaluation,
    EvidenceTier,
    LifecycleStage,
    QECategory,
    RadarItem,
    RadarRing,
    SignalDossier,
    TrendTopic,
)
from radar.pipeline.categorizer import RadarCategorizer


@pytest.fixture
def high_signal_dossier() -> SignalDossier:
    return SignalDossier(
        source_id=uuid4(),
        name="AutoMut-ADS",
        category=QECategory.EXECUTION_AND_OPTIMIZATION,
        source_url="https://arxiv.org/abs/2410.18021",
        evidence_tier=EvidenceTier.ACADEMIC_PEER_REVIEWED,
        key_innovation="Automated mutation synthesis optimizing test coverage on sensor perception loops.",
        technical_claims=["Kills 84% of mutants"],
        has_reproducible_benchmark=True,
        has_open_source_repo=True,
        is_superficial_wrapper=False,
        engagement_metrics={"velocity": 30.0},
    )


@pytest.fixture
def sample_topic() -> TrendTopic:
    return TrendTopic(
        name="Perception Mutation Testing",
        category=QECategory.EXECUTION_AND_OPTIMIZATION,
        summary="Automated mutation synthesis and clustering for autonomous perception loops.",
        corroboration_count=3,
        sources=[
            "https://arxiv.org/abs/2410.18021",
            "https://github.com/org/repo",
            "https://blog.com/post",
        ],
        average_viability=0.85,
        average_validity=0.85,
        lifecycle_stage=LifecycleStage.CONSOLIDATED,
    )


@pytest.fixture
def high_viability_evaluation(high_signal_dossier: SignalDossier) -> EnterpriseEvaluation:
    return EnterpriseEvaluation(
        dossier_id=high_signal_dossier.id,
        security_score=0.90,
        cicd_score=0.85,
        qe_score=0.90,
        composite_viability_score=0.88,
        enterprise_risks=[],
        prerequisites=[],
        skeptic_critique="Meets tier-1 enterprise standards.",
    )


def test_categorizer_assigns_adopt_ring(
    high_signal_dossier: SignalDossier,
    sample_topic: TrendTopic,
    high_viability_evaluation: EnterpriseEvaluation,
) -> None:
    categorizer = RadarCategorizer()
    item = categorizer.categorize(
        dossier=high_signal_dossier,
        evaluation=high_viability_evaluation,
        topic=sample_topic,
    )

    assert isinstance(item, RadarItem)
    assert item.recommended_ring == RadarRing.ADOPT
    assert item.viability_score == 0.88
    # Baseline 0.50 + 0.30 (peer reviewed bench) + 0.25 (corroboration >= 3) + 0.20 (velocity >= 25) = 1.0 clamped
    assert item.validity_score == 1.0
    assert item.hype_score == 0.0
    assert item.lifecycle_stage == LifecycleStage.CONSOLIDATED  # Topic has corroboration >= 3


def test_categorizer_assigns_trial_ring(high_signal_dossier: SignalDossier) -> None:
    categorizer = RadarCategorizer()
    trial_eval = EnterpriseEvaluation(
        dossier_id=high_signal_dossier.id,
        security_score=0.70,
        cicd_score=0.65,
        qe_score=0.75,
        composite_viability_score=0.70,
        enterprise_risks=["Minor runner setup"],
        prerequisites=[],
        skeptic_critique="Good for non-critical pipelines.",
    )

    item = categorizer.categorize(
        dossier=high_signal_dossier,
        evaluation=trial_eval,
        topic=None,
    )

    assert item.recommended_ring == RadarRing.TRIAL
    assert item.viability_score == 0.70


def test_categorizer_assigns_assess_ring() -> None:
    categorizer = RadarCategorizer()
    early_dossier = SignalDossier(
        source_id=uuid4(),
        name="EmergingTestLab",
        category=QECategory.AGENT_SYSTEMS,
        source_url="https://arxiv.org/abs/2411.0001",
        evidence_tier=EvidenceTier.ACADEMIC_PEER_REVIEWED,
        key_innovation="Agentic code exploration framework.",
        has_reproducible_benchmark=False,
        has_open_source_repo=True,
        is_superficial_wrapper=False,
        engagement_metrics={"velocity": 35.0},
    )
    assess_eval = EnterpriseEvaluation(
        dossier_id=early_dossier.id,
        security_score=0.50,
        cicd_score=0.50,
        qe_score=0.60,
        composite_viability_score=0.53,
        enterprise_risks=["Emerging paradigm"],
        prerequisites=[],
        skeptic_critique="Monitor closely.",
    )

    item = categorizer.categorize(dossier=early_dossier, evaluation=assess_eval)
    assert item.recommended_ring == RadarRing.ASSESS
    assert item.lifecycle_stage == LifecycleStage.EMERGING


def test_categorizer_assigns_hold_ring_for_wrapper() -> None:
    categorizer = RadarCategorizer()
    wrapper_dossier = SignalDossier(
        source_id=uuid4(),
        name="RepackagedAI Test SaaS",
        category=QECategory.TEST_SYNTHESIS,
        source_url="https://vendor.com/repackage",
        evidence_tier=EvidenceTier.VENDOR_ANNOUNCEMENT,
        key_innovation="Commercial wrapper around standard GPT-4 prompt.",
        has_reproducible_benchmark=False,
        has_open_source_repo=False,
        is_superficial_wrapper=True,
        engagement_metrics={"velocity": 2.0},
    )
    hold_eval = EnterpriseEvaluation(
        dossier_id=wrapper_dossier.id,
        security_score=0.30,
        cicd_score=0.30,
        qe_score=0.30,
        composite_viability_score=0.30,
        enterprise_risks=["Vendor lock-in", "Third-party egress"],
        prerequisites=[],
        skeptic_critique="Superficial wrapper without novelty.",
    )

    item = categorizer.categorize(dossier=wrapper_dossier, evaluation=hold_eval)
    assert item.recommended_ring == RadarRing.HOLD
    assert item.lifecycle_stage == LifecycleStage.FADING
    assert item.hype_score >= 0.70  # High hype due to deductions


def test_categorizer_assigns_adopt_for_established_repo_with_high_stars(
    high_signal_dossier: SignalDossier,
    high_viability_evaluation: EnterpriseEvaluation,
) -> None:
    categorizer = RadarCategorizer()
    # Corroboration=1, but stars=1500 >= 500 threshold -> CONSOLIDATED
    high_signal_dossier.engagement_metrics["stars"] = 1500.0
    item = categorizer.categorize(
        dossier=high_signal_dossier,
        evaluation=high_viability_evaluation,
        topic=None,
    )
    assert item.lifecycle_stage == LifecycleStage.CONSOLIDATED
    assert item.recommended_ring == RadarRing.ADOPT
    assert item.viability_score == 0.88


def test_categorizer_assigns_trial_to_high_viability_emerging_innovation(
    high_signal_dossier: SignalDossier,
    high_viability_evaluation: EnterpriseEvaluation,
) -> None:
    categorizer = RadarCategorizer()
    # High viability (0.88), low hype (0.0), but topic=None -> corroboration=1 -> EMERGING
    item = categorizer.categorize(
        dossier=high_signal_dossier,
        evaluation=high_viability_evaluation,
        topic=None,
    )

    assert item.lifecycle_stage == LifecycleStage.EMERGING
    # Under ADR-0022, high viability emerging items enter TRIAL (candidate pilot), NOT Adopt
    assert item.recommended_ring == RadarRing.TRIAL
    assert item.viability_score == 0.88


def test_categorize_batch(
    high_signal_dossier: SignalDossier,
    high_viability_evaluation: EnterpriseEvaluation,
) -> None:
    categorizer = RadarCategorizer()
    items = categorizer.categorize_batch(
        dossiers=[high_signal_dossier],
        evaluations=[high_viability_evaluation],
    )

    assert len(items) == 1
    assert items[0].name == high_signal_dossier.name
    assert items[0].active is True


def test_categorizer_inherits_topic_consensus_category(
    high_signal_dossier: SignalDossier,
    high_viability_evaluation: EnterpriseEvaluation,
) -> None:
    categorizer = RadarCategorizer()

    # Dossier has initial noisy category
    high_signal_dossier.category = QECategory.TEST_SYNTHESIS

    # Topic consensus category is TRIAGE_AND_FIX
    topic = TrendTopic(
        name="Automated Failure Diagnosis & Self-Healing",
        category=QECategory.TRIAGE_AND_FIX,
        summary="Automated triage and repair.",
        corroboration_count=2,
        average_viability=0.85,
        average_validity=0.85,
    )

    item_with_topic = categorizer.categorize(
        dossier=high_signal_dossier,
        evaluation=high_viability_evaluation,
        topic=topic,
    )
    assert item_with_topic.category == QECategory.TRIAGE_AND_FIX
    assert item_with_topic.topic_name == "Automated Failure Diagnosis & Self-Healing"

    # Without topic, falls back to dossier category
    item_without_topic = categorizer.categorize(
        dossier=high_signal_dossier,
        evaluation=high_viability_evaluation,
        topic=None,
    )
    assert item_without_topic.category == QECategory.TEST_SYNTHESIS


def test_consolidate_canonical_exemplars_under_limit() -> None:
    categorizer = RadarCategorizer(max_exemplars_per_topic=4)
    items = [
        RadarItem(
            name=f"Tool-{i}",
            topic_name="Property-Based Testing",
            category=QECategory.SPEC_AND_MODEL,
            source_url=f"https://github.com/org/tool-{i}",
            evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
            hype_score=0.2,
            viability_score=0.8,
            validity_score=0.8,
            recommended_ring=RadarRing.TRIAL,
            key_innovation="Property testing",
        )
        for i in range(3)
    ]
    consolidated = categorizer.consolidate_canonical_exemplars(items)
    assert len(consolidated) == 3
    assert all(it.is_canonical is True for it in consolidated)


def test_consolidate_canonical_exemplars_oversaturated_topic() -> None:
    categorizer = RadarCategorizer(max_exemplars_per_topic=3)
    # 7 items in the same topic with multi-variants from stryker and pitest
    raw_items = [
        RadarItem(
            name="stryker-mutator/stryker-js",
            topic_name="Automated Mutation Testing",
            category=QECategory.EXECUTION_AND_OPTIMIZATION,
            source_url="https://github.com/stryker-mutator/stryker-js",
            evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
            hype_score=0.1,
            viability_score=0.92,
            validity_score=0.9,
            recommended_ring=RadarRing.ADOPT,
            velocity_score=80.0,
            key_innovation="Stryker JS mutation runner",
        ),
        RadarItem(
            name="stryker-mutator/stryker-net",
            topic_name="Automated Mutation Testing",
            category=QECategory.EXECUTION_AND_OPTIMIZATION,
            source_url="https://github.com/stryker-mutator/stryker-net",
            evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
            hype_score=0.15,
            viability_score=0.88,
            validity_score=0.85,
            recommended_ring=RadarRing.ADOPT,
            velocity_score=70.0,
            key_innovation="Stryker .NET mutation runner",
        ),
        RadarItem(
            name="hcoles/pitest",
            topic_name="Automated Mutation Testing",
            category=QECategory.EXECUTION_AND_OPTIMIZATION,
            source_url="https://github.com/hcoles/pitest",
            evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
            hype_score=0.15,
            viability_score=0.89,
            validity_score=0.85,
            recommended_ring=RadarRing.ADOPT,
            velocity_score=50.0,
            key_innovation="PIT Mutation testing for Java",
        ),
        RadarItem(
            name="mbj/mutant",
            topic_name="Automated Mutation Testing",
            category=QECategory.EXECUTION_AND_OPTIMIZATION,
            source_url="https://github.com/mbj/mutant",
            evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
            hype_score=0.2,
            viability_score=0.85,
            validity_score=0.8,
            recommended_ring=RadarRing.TRIAL,
            velocity_score=60.0,
            key_innovation="Mutant for Ruby",
        ),
        RadarItem(
            name="szpak/gradle-pitest-plugin",
            topic_name="Automated Mutation Testing",
            category=QECategory.EXECUTION_AND_OPTIMIZATION,
            source_url="https://github.com/szpak/gradle-pitest-plugin",
            evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
            hype_score=0.3,
            viability_score=0.75,
            validity_score=0.7,
            recommended_ring=RadarRing.TRIAL,
            velocity_score=15.0,
            key_innovation="Gradle plugin for PIT",
        ),
        RadarItem(
            name="student/mutation-demo",
            topic_name="Automated Mutation Testing",
            category=QECategory.EXECUTION_AND_OPTIMIZATION,
            source_url="https://github.com/student/mutation-demo",
            evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
            hype_score=0.4,
            viability_score=0.5,
            validity_score=0.5,
            recommended_ring=RadarRing.HOLD,
            velocity_score=1.0,
            key_innovation="Class experiment",
        ),
        RadarItem(
            name="boxed/mutmut",
            topic_name="Automated Mutation Testing",
            category=QECategory.EXECUTION_AND_OPTIMIZATION,
            source_url="https://github.com/boxed/mutmut",
            evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
            hype_score=0.2,
            viability_score=0.84,
            validity_score=0.8,
            recommended_ring=RadarRing.TRIAL,
            velocity_score=40.0,
            key_innovation="Mutmut Python mutation testing",
        ),
    ]

    consolidated = categorizer.consolidate_canonical_exemplars(raw_items, max_exemplars_per_topic=3)
    canonical = [it for it in consolidated if it.is_canonical]
    non_canonical = [it for it in consolidated if not it.is_canonical]

    assert len(canonical) == 3
    assert len(non_canonical) == 4

    # Verify namespace diversity: stryker-js was chosen, so stryker-net was penalized and not elected in top 3
    canonical_names = [it.name for it in canonical]
    assert "stryker-mutator/stryker-js" in canonical_names
    assert "hcoles/pitest" in canonical_names
    assert "stryker-mutator/stryker-net" not in canonical_names

    # Corroborating sources roll-up: each canonical exemplar must contain non-canonical URLs
    for cit in canonical:
        assert len(cit.corroborating_sources) >= 4
        assert "https://github.com/student/mutation-demo" in cit.corroborating_sources
