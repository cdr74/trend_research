"""Unit tests for the Stage 3 pgvector Topic Convergence and Wrapper Detection Engine."""

import math
from uuid import uuid4

import pytest

from radar.core.config import settings
from radar.core.models import (
    EvidenceTier,
    QECategory,
    SignalDossier,
)
from radar.pipeline.convergence import (
    TopicConvergenceEngine,
    compute_cosine_similarity,
)
from radar.providers.mock import MockProvider


def make_unit_vector(dim: int, index: int) -> list[float]:
    """Helper to generate an orthogonal one-hot unit vector."""
    vec = [0.0] * dim
    vec[index] = 1.0
    return vec


def make_blended_vector(dim: int, base_idx: int, blend_idx: int, weight: float) -> list[float]:
    """Helper to generate a normalized blended vector with controlled cosine similarity."""
    vec = [0.0] * dim
    vec[base_idx] = math.sqrt(1.0 - (weight**2))
    vec[blend_idx] = weight
    return vec


@pytest.fixture
def mock_provider() -> MockProvider:
    return MockProvider(embedding_dim=1536)


def test_compute_cosine_similarity() -> None:
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert pytest.approx(compute_cosine_similarity(v1, v2)) == 1.0

    v3 = [0.0, 1.0, 0.0]
    assert pytest.approx(compute_cosine_similarity(v1, v3)) == 0.0

    v4 = [1.0, 1.0, 0.0]
    assert pytest.approx(compute_cosine_similarity(v1, v4)) == 1.0 / math.sqrt(2.0)

    # Empty / mismatched vectors
    assert compute_cosine_similarity([], []) == 0.0
    assert compute_cosine_similarity([1.0], [1.0, 2.0]) == 0.0


@pytest.mark.asyncio
async def test_first_dossier_seeds_new_topic(mock_provider: MockProvider) -> None:
    engine = TopicConvergenceEngine(provider=mock_provider)

    dossier = SignalDossier(
        source_id=uuid4(),
        name="AutoMut-ADS",
        category=QECategory.EXECUTION_AND_OPTIMIZATION,
        source_url="https://arxiv.org/abs/2410.18021",
        evidence_tier=EvidenceTier.ACADEMIC_PEER_REVIEWED,
        key_innovation="Automated mutation synthesis optimizing test coverage.",
        technical_claims=["Kills 84% of mutants"],
        has_reproducible_benchmark=True,
        has_open_source_repo=True,
        embedding=make_unit_vector(1536, 0),
    )

    result = await engine.converge_dossier(dossier)

    assert result.is_new_topic is True
    assert result.corroboration_count == 1
    assert result.is_wrapper is False
    assert result.similarity_score == 0.0
    assert dossier.topic_id == result.topic_id

    topic = engine.get_topic(result.topic_id)
    assert topic is not None
    assert topic.corroboration_count == 1
    assert "https://arxiv.org/abs/2410.18021" in topic.sources


@pytest.mark.asyncio
async def test_convergent_dossiers_cluster_into_single_topic(
    mock_provider: MockProvider,
) -> None:
    engine = TopicConvergenceEngine(provider=mock_provider)

    # Base academic dossier
    base_vec = make_unit_vector(1536, 0)
    dossier1 = SignalDossier(
        source_id=uuid4(),
        name="AutoMut-ADS",
        category=QECategory.EXECUTION_AND_OPTIMIZATION,
        source_url="https://arxiv.org/abs/2410.18021",
        evidence_tier=EvidenceTier.ACADEMIC_PEER_REVIEWED,
        key_innovation="Automated mutation testing for autonomous perception.",
        has_reproducible_benchmark=True,
        has_open_source_repo=True,
        embedding=base_vec,
    )
    res1 = await engine.converge_dossier(dossier1)

    # Corroborating open-source repo with cosine similarity ~ 0.85 (above 0.82 threshold)
    # Cosine similarity = sqrt(1 - 0.25^2) = sqrt(0.9375) ~ 0.968
    convergent_vec = make_blended_vector(1536, 0, 1, weight=0.25)
    dossier2 = SignalDossier(
        source_id=uuid4(),
        name="mut-perception-framework",
        category=QECategory.EXECUTION_AND_OPTIMIZATION,
        source_url="https://github.com/autonomous/mut-perception",
        evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
        key_innovation="Open source perception mutation harness based on AutoMut.",
        has_reproducible_benchmark=True,
        has_open_source_repo=True,
        embedding=convergent_vec,
    )
    res2 = await engine.converge_dossier(dossier2)

    assert res2.is_new_topic is False
    assert res2.topic_id == res1.topic_id
    assert res2.corroboration_count == 2
    assert res2.similarity_score > 0.82
    assert res2.is_wrapper is False

    topic = engine.get_topic(res1.topic_id)
    assert topic is not None
    assert topic.corroboration_count == 2
    assert len(topic.sources) == 2


@pytest.mark.asyncio
async def test_parasitic_wrapper_detection(mock_provider: MockProvider) -> None:
    engine = TopicConvergenceEngine(provider=mock_provider)

    # Legitimate root open-source innovation
    root_vec = make_unit_vector(1536, 0)
    root_dossier = SignalDossier(
        source_id=uuid4(),
        name="DeepTest-Engine",
        category=QECategory.TEST_SYNTHESIS,
        source_url="https://github.com/org/deeptest",
        evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
        key_innovation="Novel coverage-guided test generator for neural architectures.",
        has_reproducible_benchmark=True,
        has_open_source_repo=True,
        is_superficial_wrapper=False,
        embedding=root_vec,
    )
    res_root = await engine.converge_dossier(root_dossier)

    # Parasitic vendor wrapper with 0.95 similarity, no benchmark, no repo
    wrapper_vec = make_blended_vector(1536, 0, 1, weight=0.1)  # sim ~ 0.995
    wrapper_dossier = SignalDossier(
        source_id=uuid4(),
        name="AutoTestEnterprise Cloud",
        category=QECategory.TEST_SYNTHESIS,
        source_url="https://commercialvendor.com/autotest",
        evidence_tier=EvidenceTier.VENDOR_ANNOUNCEMENT,
        key_innovation="Commercial cloud AI test generator using neural architectures.",
        has_reproducible_benchmark=False,
        has_open_source_repo=False,
        is_superficial_wrapper=False,  # Unmarked upfront, must be caught by engine
        embedding=wrapper_vec,
    )
    res_wrapper = await engine.converge_dossier(wrapper_dossier)

    assert res_wrapper.is_new_topic is False
    assert res_wrapper.topic_id == res_root.topic_id
    assert res_wrapper.similarity_score >= 0.88
    assert res_wrapper.is_wrapper is True
    assert res_wrapper.wrapper_penalty_applied == settings.wrapper_penalty
    assert wrapper_dossier.is_superficial_wrapper is True


@pytest.mark.asyncio
async def test_post_mortem_protected_from_wrapper_penalty(
    mock_provider: MockProvider,
) -> None:
    engine = TopicConvergenceEngine(provider=mock_provider)

    # Root open-source innovation
    root_vec = make_unit_vector(1536, 0)
    root_dossier = SignalDossier(
        source_id=uuid4(),
        name="Quasar-API-Analysis",
        category=QECategory.TEST_SYNTHESIS,
        source_url="https://github.com/org/quasar",
        evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
        key_innovation="Dependency graph API blast radius analysis.",
        has_reproducible_benchmark=False,
        has_open_source_repo=True,
        is_superficial_wrapper=False,
        embedding=root_vec,
    )
    res_root = await engine.converge_dossier(root_dossier)

    # Engineering post-mortem with high similarity (no standalone repo or benchmark)
    post_mortem_vec = make_blended_vector(1536, 0, 1, weight=0.1)  # sim ~ 0.995
    post_mortem_dossier = SignalDossier(
        source_id=uuid4(),
        name="Netflix Engineering Blast Radius Tool Post-Mortem",
        category=QECategory.TEST_SYNTHESIS,
        source_url="https://netflixtechblog.com/beyond-api-compatibility",
        evidence_tier=EvidenceTier.ENGINEERING_POST_MORTEM,
        key_innovation="Production lessons from measuring blast radius of library changes.",
        has_reproducible_benchmark=False,
        has_open_source_repo=False,
        is_superficial_wrapper=False,
        embedding=post_mortem_vec,
    )
    res_post_mortem = await engine.converge_dossier(post_mortem_dossier)

    assert res_post_mortem.is_new_topic is False
    assert res_post_mortem.topic_id == res_root.topic_id
    assert res_post_mortem.similarity_score >= 0.88
    # Post-mortem should NOT be marked as a superficial wrapper under ADR-0022
    assert res_post_mortem.is_wrapper is False
    assert res_post_mortem.wrapper_penalty_applied == 0.0
    assert post_mortem_dossier.is_superficial_wrapper is False


@pytest.mark.asyncio
async def test_multi_source_cross_channel_consensus_bonus(
    mock_provider: MockProvider,
) -> None:
    engine = TopicConvergenceEngine(provider=mock_provider)

    base_vec = make_unit_vector(1536, 0)

    # 1. Academic paper (arXiv)
    arxiv_dossier = SignalDossier(
        source_id=uuid4(),
        name="GNN-Test-Selection-Paper",
        category=QECategory.EXECUTION_AND_OPTIMIZATION,
        source_url="https://arxiv.org/abs/2405.0001",
        evidence_tier=EvidenceTier.ACADEMIC_PEER_REVIEWED,
        key_innovation="Graph neural network based predictive test selection.",
        has_reproducible_benchmark=True,
        has_open_source_repo=True,
        embedding=base_vec,
    )
    await engine.converge_dossier(arxiv_dossier)

    # 2. Open source repo (GitHub)
    gh_dossier = SignalDossier(
        source_id=uuid4(),
        name="gnn-test-selector",
        category=QECategory.EXECUTION_AND_OPTIMIZATION,
        source_url="https://github.com/org/gnn-test-selector",
        evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
        key_innovation="Implementation of GNN test selector.",
        has_reproducible_benchmark=True,
        has_open_source_repo=True,
        embedding=make_blended_vector(1536, 0, 1, weight=0.15),
    )
    await engine.converge_dossier(gh_dossier)

    # 3. Engineering post-mortem / Blog (RSS)
    rss_dossier = SignalDossier(
        source_id=uuid4(),
        name="Netflix GNN PTS Experience",
        category=QECategory.EXECUTION_AND_OPTIMIZATION,
        source_url="https://netflixtechblog.com/gnn-pts-experience",
        evidence_tier=EvidenceTier.ENGINEERING_POST_MORTEM,
        key_innovation="Production deployment of GNN predictive test selection at Netflix.",
        has_reproducible_benchmark=True,
        has_open_source_repo=False,
        embedding=make_blended_vector(1536, 0, 1, weight=0.20),
    )
    res_rss = await engine.converge_dossier(rss_dossier)

    assert res_rss.multi_source_consensus is True
    assert res_rss.corroboration_count == 3

    topic = engine.get_topic(res_rss.topic_id)
    assert topic is not None
    # 0.5 baseline + 0.25 consensus bonus
    assert topic.average_validity >= 0.75


@pytest.mark.asyncio
async def test_configurable_threshold_overrides(mock_provider: MockProvider) -> None:
    # Stricter threshold: require 0.98 similarity to converge
    engine = TopicConvergenceEngine(
        provider=mock_provider,
        convergence_threshold=0.98,
    )

    base_vec = make_unit_vector(1536, 0)
    dossier1 = SignalDossier(
        source_id=uuid4(),
        name="ToolA",
        category=QECategory.TEST_SYNTHESIS,
        source_url="https://arxiv.org/abs/1",
        evidence_tier=EvidenceTier.ACADEMIC_PEER_REVIEWED,
        key_innovation="Tool A innovation.",
        embedding=base_vec,
    )
    res1 = await engine.converge_dossier(dossier1)

    # Similarity is ~0.95 (above standard 0.82, but below strict 0.98)
    dossier2 = SignalDossier(
        source_id=uuid4(),
        name="ToolB",
        category=QECategory.TEST_SYNTHESIS,
        source_url="https://arxiv.org/abs/2",
        evidence_tier=EvidenceTier.ACADEMIC_PEER_REVIEWED,
        key_innovation="Tool B innovation.",
        embedding=make_blended_vector(1536, 0, 1, weight=0.30),
    )
    res2 = await engine.converge_dossier(dossier2)

    # Must create a separate topic because it fails the strict 0.98 threshold
    assert res2.is_new_topic is True
    assert res2.topic_id != res1.topic_id


@pytest.mark.asyncio
async def test_bounded_themes_condensation_under_cap(mock_provider: MockProvider) -> None:
    """Verify that condensation merges closest topic pairs when count exceeds max_themes."""
    engine = TopicConvergenceEngine(
        provider=mock_provider,
        convergence_threshold=0.90,
        max_themes=3,
    )

    dossiers: list[SignalDossier] = []
    # Create 5 dossiers on orthogonal indices
    for i in range(5):
        dossiers.append(
            SignalDossier(
                source_id=uuid4(),
                name=f"Tool_{i}",
                category=QECategory.TEST_SYNTHESIS,
                source_url=f"https://example.com/tool_{i}",
                evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
                key_innovation=f"Key innovation {i}",
                embedding=make_unit_vector(1536, i),
            )
        )

    # Add a 6th dossier very close to index 0 (weight 0.1 -> sim ~0.995)
    dossiers.append(
        SignalDossier(
            source_id=uuid4(),
            name="Tool_0_variant",
            category=QECategory.TEST_SYNTHESIS,
            source_url="https://example.com/tool_0_v",
            evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
            key_innovation="Variant of key innovation 0",
            embedding=make_blended_vector(1536, 0, 10, weight=0.1),
        )
    )

    results = await engine.converge_batch(dossiers)
    assert len(results) == 6
    # engine._topics must be bounded by max_themes
    assert len(engine._topics) <= 3
    # Every dossier must have topic_name assigned
    for d in engine._dossiers.values():
        assert d.topic_name is not None
        assert len(d.topic_name) > 0


@pytest.mark.asyncio
async def test_dynamic_theme_attribution_on_convergence(mock_provider: MockProvider) -> None:
    """Verify that dossiers receive topic_name attribute matching their converged topic."""
    engine = TopicConvergenceEngine(provider=mock_provider, convergence_threshold=0.65)

    d1 = SignalDossier(
        source_id=uuid4(),
        name="stryker-js",
        category=QECategory.EXECUTION_AND_OPTIMIZATION,
        source_url="https://github.com/stryker-mutator/stryker-js",
        evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
        key_innovation="Mutation testing for JavaScript and TypeScript.",
        embedding=make_unit_vector(1536, 0),
    )
    d2 = SignalDossier(
        source_id=uuid4(),
        name="pitest",
        category=QECategory.EXECUTION_AND_OPTIMIZATION,
        source_url="https://github.com/hcoles/pitest",
        evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
        key_innovation="Mutation testing system for Java and the JVM.",
        embedding=make_blended_vector(1536, 0, 1, weight=0.1),
    )

    await engine.converge_dossier(d1)
    await engine.converge_dossier(d2)

    assert d1.topic_id == d2.topic_id
    assert d1.topic_name == d2.topic_name
    assert d1.topic_name is not None
