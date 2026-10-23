"""Unit tests for Pydantic v2 domain models and schema validation."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

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


def test_source_payload_creation() -> None:
    payload = SourcePayload(
        source_type=SourceType.ARXIV,
        source_url="https://arxiv.org/abs/2401.00001",
        title="Agentic Mutation Testing with Formal Guarantees",
        raw_content="Abstract discussing automated mutation testing...",
    )
    assert payload.source_type == SourceType.ARXIV
    assert payload.id is not None
    assert "arxiv" in payload.source_url


def test_signal_dossier_creation() -> None:
    source_id = uuid4()
    dossier = SignalDossier(
        source_id=source_id,
        name="AutoMutate-Agent",
        category=QECategory.EXECUTION_AND_OPTIMIZATION,
        source_url="https://github.com/example/automutate",
        evidence_tier=EvidenceTier.ACADEMIC_PEER_REVIEWED,
        key_innovation="LLM-guided semantic mutation reduction.",
        technical_claims=["Reduces mutant search space by 80%."],
        has_reproducible_benchmark=True,
        has_open_source_repo=True,
    )
    assert dossier.category == QECategory.EXECUTION_AND_OPTIMIZATION
    assert dossier.has_open_source_repo is True
    assert dossier.source_id == source_id


def test_enterprise_evaluation_score_bounds() -> None:
    dossier_id = uuid4()
    # Valid evaluation
    eval_record = EnterpriseEvaluation(
        dossier_id=dossier_id,
        topology_score=0.9,
        determinism_score=0.85,
        privacy_score=0.95,
        auditability_score=0.8,
        composite_viability_score=0.88,
        enterprise_risks=["Requires self-hosted Ollama deployment."],
        skeptic_critique="Meets zero-egress banking criteria.",
    )
    assert eval_record.composite_viability_score == 0.88

    # Invalid score > 1.0
    with pytest.raises(ValidationError):
        EnterpriseEvaluation(
            dossier_id=dossier_id,
            topology_score=1.5,
            determinism_score=0.5,
            privacy_score=0.5,
            auditability_score=0.5,
            composite_viability_score=0.5,
            skeptic_critique="Out of bounds",
        )

    # Invalid score < 0.0
    with pytest.raises(ValidationError):
        EnterpriseEvaluation(
            dossier_id=dossier_id,
            topology_score=-0.2,
            determinism_score=0.5,
            privacy_score=0.5,
            auditability_score=0.5,
            composite_viability_score=0.5,
            skeptic_critique="Out of bounds",
        )


def test_radar_item_creation_and_json_serialization() -> None:
    item = RadarItem(
        name="TestGenius",
        category=QECategory.TEST_SYNTHESIS,
        source_url="https://github.com/testgenius/testgenius",
        evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
        hype_score=0.25,
        viability_score=0.85,
        validity_score=0.75,
        recommended_ring=RadarRing.ADOPT,
        key_innovation="Differential unit test synthesis with property-based boundary search.",
        enterprise_risks=["Requires local repository indexing."],
    )
    assert item.recommended_ring == RadarRing.ADOPT
    assert item.hype_score == 0.25

    # Check serialization
    json_data = item.model_dump_json()
    assert "TestGenius" in json_data
    assert "Adopt" in json_data
