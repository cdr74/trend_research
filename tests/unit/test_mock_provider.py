"""Unit tests for the deterministic mock provider."""

import pytest

from radar.core.models import RadarItem
from radar.providers.mock import MockProvider


@pytest.mark.asyncio
async def test_mock_provider_generate_text(mock_provider: MockProvider) -> None:
    res = await mock_provider.generate_text("Explain flaky test isolation")
    assert "[MOCK RESPONSE]" in res
    assert "Explain flaky test isolation" in res


@pytest.mark.asyncio
async def test_mock_provider_generate_structured(mock_provider: MockProvider) -> None:
    res = await mock_provider.generate_structured(
        prompt="Generate dummy radar item",
        response_model=RadarItem,
    )
    assert isinstance(res, RadarItem)
    assert res.name == "Mock Data"
    assert res.hype_score == 0.75


@pytest.mark.asyncio
async def test_mock_provider_embed_text(mock_provider: MockProvider) -> None:
    embedding = await mock_provider.embed_text("Sample technical signal")
    assert len(embedding) == mock_provider.embedding_dim
    assert isinstance(embedding[0], float)


@pytest.mark.asyncio
async def test_mock_provider_embed_text_thematic_clustering(mock_provider: MockProvider) -> None:
    vec_mut1 = await mock_provider.embed_text("pitest java mutation testing tool")
    vec_mut2 = await mock_provider.embed_text("stryker mutant test suite")
    vec_browser = await mock_provider.embed_text("playwright autonomous browser agent")

    # Cosine similarity for unit vectors is dot product
    sim_same = sum(a * b for a, b in zip(vec_mut1, vec_mut2, strict=False))
    sim_diff = sum(a * b for a, b in zip(vec_mut1, vec_browser, strict=False))

    assert sim_same > 0.80
    assert sim_diff < 0.40


@pytest.mark.asyncio
async def test_mock_provider_fuzzing_and_triage_alignment(mock_provider: MockProvider) -> None:
    from radar.core.models import ExtractedInnovation, QECategory, SynthesizedTopic

    # Test Fuzzing / JQF extraction & topic synthesis
    fuzz_extracted = await mock_provider.generate_structured(
        prompt="Title: rohanpadhye/JQF\nContent Body / Abstract: Coverage-guided semantic fuzzing for Java.",
        response_model=ExtractedInnovation,
    )
    assert fuzz_extracted.category == QECategory.TEST_SYNTHESIS

    fuzz_topic = await mock_provider.generate_structured(
        prompt="Convergent Innovations:\n- Name: rohanpadhye/JQF | Key Innovation: JQF + Zest fuzzing.",
        response_model=SynthesizedTopic,
    )
    assert fuzz_topic.name == "Coverage-Guided Fuzzing & Dynamic Test Generation"
    assert fuzz_topic.primary_category == QECategory.TEST_SYNTHESIS

    # Test Triage / ReportPortal extraction & topic synthesis
    triage_extracted = await mock_provider.generate_structured(
        prompt="Title: reportportal/reportportal\nContent Body / Abstract: AI-based test automation dashboard and failure triage.",
        response_model=ExtractedInnovation,
    )
    assert triage_extracted.category == QECategory.TRIAGE_AND_FIX

    triage_topic = await mock_provider.generate_structured(
        prompt="Convergent Innovations:\n- Name: reportportal | Key Innovation: Automated triage and defect classification.",
        response_model=SynthesizedTopic,
    )
    assert triage_topic.name == "Automated Failure Diagnosis & Self-Healing"
    assert triage_topic.primary_category == QECategory.TRIAGE_AND_FIX

    # Test Fuzzing vs Triage embedding discrimination
    vec_fuzz1 = await mock_provider.embed_text("rohanpadhye/JQF coverage-guided fuzzing")
    vec_fuzz2 = await mock_provider.embed_text("fuzzcheck-rs evolutionary fuzzer")
    vec_triage = await mock_provider.embed_text("reportportal automated triage and log root cause")

    sim_fuzz = sum(a * b for a, b in zip(vec_fuzz1, vec_fuzz2, strict=False))
    sim_cross = sum(a * b for a, b in zip(vec_fuzz1, vec_triage, strict=False))

    assert sim_fuzz > 0.80
    assert sim_cross < 0.40
