"""Unit tests for the Stage 3 Multi-Lens Evaluator Committee."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from radar.core.models import (
    CommitteeAuditResult,
    EnterpriseEvaluation,
    EvidenceTier,
    LifecycleStage,
    QECategory,
    SignalDossier,
    TrendTopic,
)
from radar.pipeline.evaluator import MultiLensEvaluator
from radar.providers.mock import MockProvider


@pytest.fixture
def sample_dossier() -> SignalDossier:
    return SignalDossier(
        source_id=uuid4(),
        name="AutoMut-ADS",
        category=QECategory.EXECUTION_AND_OPTIMIZATION,
        source_url="https://arxiv.org/abs/2410.18021",
        evidence_tier=EvidenceTier.ACADEMIC_PEER_REVIEWED,
        key_innovation="Automated mutation synthesis optimizing test coverage on sensor fusion loops.",
        technical_claims=[
            "Kills 84% of high-order semantic mutants in sensor perception logic.",
            "Reduces regression test suite execution time by 35% through mutation clustering.",
        ],
        has_reproducible_benchmark=True,
        has_open_source_repo=True,
        is_superficial_wrapper=False,
    )


@pytest.fixture
def sample_topic() -> TrendTopic:
    return TrendTopic(
        name="Perception Mutation Testing",
        category=QECategory.EXECUTION_AND_OPTIMIZATION,
        summary="Automated mutation synthesis and clustering for autonomous perception loops.",
        corroboration_count=2,
        sources=["https://arxiv.org/abs/2410.18021"],
        average_viability=0.75,
        average_validity=0.85,
        lifecycle_stage=LifecycleStage.EMERGING,
    )


@pytest.mark.asyncio
async def test_multi_lens_evaluator_with_mock_provider(sample_dossier: SignalDossier) -> None:
    provider = MockProvider()
    evaluator = MultiLensEvaluator(provider=provider)

    evaluation = await evaluator.evaluate(sample_dossier)

    assert isinstance(evaluation, EnterpriseEvaluation)
    assert evaluation.dossier_id == sample_dossier.id
    assert 0.0 <= evaluation.composite_viability_score <= 1.0
    assert 0.0 <= evaluation.security_score <= 1.0
    assert 0.0 <= evaluation.cicd_score <= 1.0
    assert 0.0 <= evaluation.qe_score <= 1.0

    expected_composite = round(
        0.35 * evaluation.security_score
        + 0.35 * evaluation.cicd_score
        + 0.30 * evaluation.qe_score,
        4,
    )
    assert pytest.approx(evaluation.composite_viability_score) == expected_composite


@pytest.mark.asyncio
async def test_multi_lens_evaluator_prompt_and_weighting(
    sample_dossier: SignalDossier, sample_topic: TrendTopic
) -> None:
    mock_provider = AsyncMock()
    mock_audit = CommitteeAuditResult(
        security_score=0.80,
        cicd_score=0.60,
        qe_score=0.90,
        security_critique="Air-gapped safe with zero outbound telemetric egress.",
        cicd_critique="High runner memory footprint during mutation synthesis.",
        qe_critique="Solid mutation kill rate empirical benchmark on open dataset.",
        skeptic_critique="Strong potential, requires dedicated GPU runners in CI/CD pipeline.",
        enterprise_risks=["High memory usage on CI workers"],
        prerequisites=["Local GPU or dedicated high-memory runner pool"],
    )
    mock_provider.generate_structured.return_value = mock_audit

    evaluator = MultiLensEvaluator(
        provider=mock_provider,
        security_weight=0.35,
        cicd_weight=0.35,
        qe_weight=0.30,
    )

    evaluation = await evaluator.evaluate(sample_dossier, topic=sample_topic)

    # 0.35 * 0.8 + 0.35 * 0.6 + 0.30 * 0.9 = 0.28 + 0.21 + 0.27 = 0.76
    assert pytest.approx(evaluation.composite_viability_score) == 0.76
    assert evaluation.security_score == 0.80
    assert evaluation.cicd_score == 0.60
    assert evaluation.qe_score == 0.90
    assert "High memory usage" in evaluation.enterprise_risks[0]
    assert "dedicated GPU" in evaluation.skeptic_critique

    # Verify provider call and prompt contents
    mock_provider.generate_structured.assert_called_once()
    prompt_arg = mock_provider.generate_structured.call_args[0][0]
    assert "AutoMut-ADS" in prompt_arg
    assert "Perception Mutation Testing" in prompt_arg
    assert "Kills 84%" in prompt_arg


@pytest.mark.asyncio
async def test_multi_lens_evaluator_custom_weights(sample_dossier: SignalDossier) -> None:
    mock_provider = AsyncMock()
    mock_audit = CommitteeAuditResult(
        security_score=1.00,
        cicd_score=0.50,
        qe_score=0.50,
        security_critique="Air-gapped safe.",
        cicd_critique="Moderate setup friction.",
        qe_critique="Good rigor.",
        skeptic_critique="Passed security scrutiny.",
        enterprise_risks=[],
        prerequisites=[],
    )
    mock_provider.generate_structured.return_value = mock_audit

    # 50% security, 25% ops, 25% qe
    evaluator = MultiLensEvaluator(
        provider=mock_provider,
        security_weight=0.50,
        cicd_weight=0.25,
        qe_weight=0.25,
    )

    evaluation = await evaluator.evaluate(sample_dossier)
    # 0.50 * 1.0 + 0.25 * 0.5 + 0.25 * 0.5 = 0.5 + 0.125 + 0.125 = 0.75
    assert pytest.approx(evaluation.composite_viability_score) == 0.75


@pytest.mark.asyncio
async def test_multi_lens_evaluator_batch_execution(sample_dossier: SignalDossier) -> None:
    provider = MockProvider()
    evaluator = MultiLensEvaluator(provider=provider)

    batch = [sample_dossier, sample_dossier]
    evaluations = await evaluator.evaluate_batch(batch)

    assert len(evaluations) == 2
    assert all(isinstance(e, EnterpriseEvaluation) for e in evaluations)
