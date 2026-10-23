"""Unit tests for repository entity mapping and query constructors."""

from uuid import uuid4

from radar.core.models import (
    EnterpriseEvaluation,
    EvidenceTier,
    QECategory,
    RadarItem,
    RadarRing,
    SignalDossier,
    SourcePayload,
    SourceType,
)
from radar.db.tables import (
    EnterpriseEvaluationTable,
    IngestedSourceTable,
    RadarItemTable,
    SignalDossierTable,
)


def test_source_payload_to_orm_mapping() -> None:
    payload = SourcePayload(
        source_type=SourceType.GITHUB,
        source_url="https://github.com/cdr74/test-tool",
        title="Predictive Test Selection with Graph Neural Networks",
        raw_content="ReadMe content here...",
        author="cdr74",
    )
    table = IngestedSourceTable(
        id=payload.id,
        source_type=payload.source_type.value,
        source_url=payload.source_url,
        title=payload.title,
        raw_content=payload.raw_content,
        author=payload.author,
    )
    assert table.id == payload.id
    assert table.source_type == "github"
    assert table.title == payload.title


def test_signal_dossier_to_orm_mapping() -> None:
    source_id = uuid4()
    dossier = SignalDossier(
        source_id=source_id,
        name="GraphPTS",
        category=QECategory.EXECUTION_AND_OPTIMIZATION,
        source_url="https://github.com/cdr74/test-tool",
        evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
        key_innovation="GNN-based test impact analysis.",
        has_reproducible_benchmark=True,
        has_open_source_repo=True,
    )
    table = SignalDossierTable(
        id=dossier.id,
        source_id=dossier.source_id,
        name=dossier.name,
        category=dossier.category.value,
        source_url=dossier.source_url,
        evidence_tier=dossier.evidence_tier.value,
        key_innovation=dossier.key_innovation,
        has_reproducible_benchmark=dossier.has_reproducible_benchmark,
        has_open_source_repo=dossier.has_open_source_repo,
    )
    assert table.name == "GraphPTS"
    assert table.category == "Execution & Optimization"


def test_enterprise_evaluation_to_orm_mapping() -> None:
    dossier_id = uuid4()
    evaluation = EnterpriseEvaluation(
        dossier_id=dossier_id,
        topology_score=1.0,
        determinism_score=0.9,
        privacy_score=1.0,
        auditability_score=0.8,
        composite_viability_score=0.925,
        enterprise_risks=[],
        prerequisites=["Local GPU recommended"],
        skeptic_critique="Meets all Tier-1 banking constraints.",
    )
    table = EnterpriseEvaluationTable(
        id=evaluation.id,
        dossier_id=evaluation.dossier_id,
        topology_score=evaluation.topology_score,
        determinism_score=evaluation.determinism_score,
        privacy_score=evaluation.privacy_score,
        auditability_score=evaluation.auditability_score,
        composite_viability_score=evaluation.composite_viability_score,
        enterprise_risks=evaluation.enterprise_risks,
        prerequisites=evaluation.prerequisites,
        skeptic_critique=evaluation.skeptic_critique,
    )
    assert table.composite_viability_score == 0.925
    assert table.topology_score == 1.0


def test_radar_item_to_orm_mapping() -> None:
    item = RadarItem(
        name="GraphPTS",
        category=QECategory.EXECUTION_AND_OPTIMIZATION,
        source_url="https://github.com/cdr74/test-tool",
        evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
        hype_score=0.15,
        viability_score=0.925,
        validity_score=0.85,
        recommended_ring=RadarRing.ADOPT,
        key_innovation="GNN-based test impact analysis.",
    )
    table = RadarItemTable(
        id=item.id,
        name=item.name,
        category=item.category.value,
        source_url=item.source_url,
        evidence_tier=item.evidence_tier.value,
        hype_score=item.hype_score,
        viability_score=item.viability_score,
        validity_score=item.validity_score,
        recommended_ring=item.recommended_ring.value,
        key_innovation=item.key_innovation,
    )
    assert table.recommended_ring == "Adopt"
    assert table.viability_score == 0.925
