"""Unit tests for the Stage 2 Deep Extractor Agent."""

from unittest.mock import AsyncMock

import pytest

from radar.core.models import (
    EvidenceTier,
    ExtractedInnovation,
    QECategory,
    QualifiedSignal,
    SignalDossier,
    SourcePayload,
    SourceType,
)
from radar.pipeline.extractor import DeepExtractor
from radar.providers.mock import MockProvider


@pytest.fixture
def sample_qualified_signal() -> QualifiedSignal:
    payload = SourcePayload(
        source_type=SourceType.ARXIV,
        source_url="https://arxiv.org/abs/2410.18021",
        title="Automated Mutation Testing for Autonomous Driving Systems",
        raw_content="We present an empirical framework evaluating mutation score and killed mutants in autonomous control loops.",
        author="Alice Smith et al.",
        metadata={"arxiv_id": "2410.18021", "categories": ["cs.SE", "cs.AI"]},
        engagement_metrics={"citations": 0.0, "velocity": 12.5},
    )
    return QualifiedSignal(
        payload=payload,
        noise_score=0.15,
        quality_markers=["Empirical evaluation", "Mutation testing"],
    )


@pytest.mark.asyncio
async def test_deep_extractor_with_mock_provider(
    sample_qualified_signal: QualifiedSignal,
) -> None:
    provider = MockProvider(embedding_dim=1536)
    extractor = DeepExtractor(provider=provider)

    dossier = await extractor.extract(sample_qualified_signal)

    assert isinstance(dossier, SignalDossier)
    assert dossier.source_id == sample_qualified_signal.payload.id
    assert dossier.source_url == sample_qualified_signal.payload.source_url
    assert isinstance(dossier.category, QECategory)
    assert isinstance(dossier.evidence_tier, EvidenceTier)
    assert dossier.embedding is not None
    assert len(dossier.embedding) == 1536
    assert dossier.engagement_metrics["velocity"] == 12.5


@pytest.mark.asyncio
async def test_deep_extractor_prompt_and_claims_mapping(
    sample_qualified_signal: QualifiedSignal,
) -> None:
    mock_provider = AsyncMock()
    mock_extracted = ExtractedInnovation(
        name="AutoMut-ADS",
        category=QECategory.EXECUTION_AND_OPTIMIZATION,
        evidence_tier=EvidenceTier.ACADEMIC_PEER_REVIEWED,
        key_innovation="Automated mutation synthesis optimizing test coverage on sensor fusion pipelines.",
        technical_claims=[
            "Kills 84% of high-order semantic mutants in sensor perception logic.",
            "Reduces regression test suite execution time by 35% through mutation clustering.",
        ],
        has_reproducible_benchmark=True,
        has_open_source_repo=True,
        is_superficial_wrapper=False,
    )
    mock_provider.generate_structured.return_value = mock_extracted
    mock_provider.embed_text.return_value = [0.123] * 1536

    extractor = DeepExtractor(provider=mock_provider)
    dossier = await extractor.extract(sample_qualified_signal)

    assert dossier.name == "AutoMut-ADS"
    assert dossier.category == QECategory.EXECUTION_AND_OPTIMIZATION
    assert dossier.evidence_tier == EvidenceTier.ACADEMIC_PEER_REVIEWED
    assert dossier.has_reproducible_benchmark is True
    assert dossier.has_open_source_repo is True
    assert dossier.is_superficial_wrapper is False
    assert len(dossier.technical_claims) == 2
    assert "Kills 84%" in dossier.technical_claims[0]

    # Verify provider calls
    mock_provider.generate_structured.assert_called_once()
    prompt_arg = mock_provider.generate_structured.call_args[0][0]
    assert "Automated Mutation Testing for Autonomous Driving Systems" in prompt_arg
    assert "arxiv" in prompt_arg

    mock_provider.embed_text.assert_called_once()
    embed_arg = mock_provider.embed_text.call_args[0][0]
    assert "AutoMut-ADS" in embed_arg
    assert "Automated mutation synthesis" in embed_arg


@pytest.mark.asyncio
async def test_deep_extractor_batch_extraction(
    sample_qualified_signal: QualifiedSignal,
) -> None:
    provider = MockProvider(embedding_dim=1536)
    extractor = DeepExtractor(provider=provider)

    batch = [sample_qualified_signal, sample_qualified_signal]
    dossiers = await extractor.extract_batch(batch)

    assert len(dossiers) == 2
    assert all(isinstance(d, SignalDossier) for d in dossiers)


@pytest.mark.asyncio
async def test_deep_extractor_accepts_raw_source_payload_directly() -> None:
    provider = MockProvider(embedding_dim=1536)
    extractor = DeepExtractor(provider=provider)

    raw_payload = SourcePayload(
        source_type=SourceType.GITHUB,
        source_url="https://github.com/microsoft/playwright",
        title="microsoft/playwright",
        raw_content="Fast and reliable end-to-end testing for modern web apps.",
    )

    dossier = await extractor.extract(raw_payload)
    assert isinstance(dossier, SignalDossier)
    assert dossier.source_id == raw_payload.id
    assert dossier.source_url == raw_payload.source_url
