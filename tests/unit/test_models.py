"""Unit tests for Pydantic v2 domain models and schema validation."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from radar.core.models import (
    EnterpriseEvaluation,
    EvidenceTier,
    LifecycleStage,
    QECategory,
    RadarItem,
    RadarRing,
    SignalDossier,
    SourcePayload,
    SourceType,
    TrendTopic,
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
    # Valid evaluation (Committee 2C: Security 35%, CI/CD 35%, QE 30%)
    eval_record = EnterpriseEvaluation(
        dossier_id=dossier_id,
        security_score=0.95,
        cicd_score=0.85,
        qe_score=0.80,
        composite_viability_score=0.87,
        enterprise_risks=["Requires self-hosted Ollama deployment."],
        skeptic_critique="Meets zero-egress banking criteria.",
        security_critique="Zero data egress verified.",
        cicd_critique="Deterministic seed execution verified.",
        qe_critique="High defect mutation score.",
    )
    assert eval_record.composite_viability_score == 0.87

    # Invalid score > 1.0
    with pytest.raises(ValidationError):
        EnterpriseEvaluation(
            dossier_id=dossier_id,
            security_score=1.5,
            cicd_score=0.5,
            qe_score=0.5,
            composite_viability_score=0.5,
            skeptic_critique="Out of bounds",
        )

    # Invalid score < 0.0
    with pytest.raises(ValidationError):
        EnterpriseEvaluation(
            dossier_id=dossier_id,
            security_score=-0.2,
            cicd_score=0.5,
            qe_score=0.5,
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
        lifecycle_stage=LifecycleStage.EMERGING,
        corroboration_count=3,
        velocity_score=42.5,
        corroborating_sources=[
            "https://arxiv.org/abs/2401.001",
            "https://blog.eng.example.com/testgenius",
        ],
        key_innovation="Differential unit test synthesis with property-based boundary search.",
        enterprise_risks=["Requires local repository indexing."],
    )
    assert item.recommended_ring == RadarRing.ADOPT
    assert item.hype_score == 0.25
    assert item.corroboration_count == 3
    assert item.lifecycle_stage == LifecycleStage.EMERGING

    # Check serialization
    json_data = item.model_dump_json()
    assert "TestGenius" in json_data
    assert "Adopt" in json_data
    assert "Emerging" in json_data


def test_trend_topic_creation() -> None:
    topic = TrendTopic(
        name="Property-Based LLM State Synthesis",
        category=QECategory.SPEC_AND_MODEL,
        summary="Automated synthesis of property-based stateful testing models from schemas.",
        corroboration_count=4,
        sources=["https://arxiv.org/abs/1", "https://github.com/tool"],
        average_viability=0.88,
        average_validity=0.82,
        lifecycle_stage=LifecycleStage.EMERGING,
    )
    assert topic.corroboration_count == 4
    assert topic.lifecycle_stage == LifecycleStage.EMERGING
