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
