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
