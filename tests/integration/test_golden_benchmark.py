"""Integration regression tests for the 20-item Golden Benchmark Suite."""

import json
import math
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from pydantic import BaseModel

from radar.core.models import (
    EvidenceTier,
    ExtractedInnovation,
    QECategory,
    RadarItem,
    RadarRing,
    SourcePayload,
    SourceType,
)
from radar.pipeline.categorizer import RadarCategorizer
from radar.pipeline.convergence import TopicConvergenceEngine
from radar.pipeline.evaluator import MultiLensEvaluator
from radar.pipeline.extractor import DeepExtractor
from radar.pipeline.noise_sieve import NoiseSieve
from radar.providers.mock import MockProvider


class DeterministicBenchmarkProvider(MockProvider):
    """Specialized mock provider for deterministic golden benchmark evaluations."""

    def __init__(self) -> None:
        super().__init__(embedding_dim=1536)

    async def embed_text(self, text: str) -> list[float]:
        """Generate pseudo-orthogonal 1536-dim unit vector based on text content."""
        seed = abs(hash(text))
        vec = [
            (float((seed * (i + 1) * 2654435761) % 1000) / 1000.0) - 0.5
            for i in range(self.embedding_dim)
        ]
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0.0:
            vec = [x / norm for x in vec]
        return vec

    async def generate_structured[T: BaseModel](
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
    ) -> T:
        if response_model is ExtractedInnovation:
            # Check prompt contents to customize output
            is_wrapper = "wrapper" in prompt.lower() or "proprietary closed" in prompt.lower()
            is_academic = "arxiv" in prompt.lower()
            has_bench = (
                "benchmark" in prompt.lower()
                or "empirical" in prompt.lower()
                or "evaluation" in prompt.lower()
                or "carla" in prompt.lower()
                or "defects4j" in prompt.lower()
                or "swe-bench" in prompt.lower()
                or is_academic
            )
            has_repo = (
                "github.com" in prompt.lower()
                or "playwright" in prompt.lower()
                or "pytest" in prompt.lower()
                or "defects4j" in prompt.lower()
            )

            tier = (
                EvidenceTier.ACADEMIC_PEER_REVIEWED
                if is_academic
                else (
                    EvidenceTier.OPEN_SOURCE_REPO
                    if has_repo
                    else (
                        EvidenceTier.ENGINEERING_POST_MORTEM
                        if "post-mortem" in prompt.lower()
                        or "netflix" in prompt.lower()
                        or "uber" in prompt.lower()
                        or "retrospective" in prompt.lower()
                        else EvidenceTier.VENDOR_ANNOUNCEMENT
                    )
                )
            )

            res = ExtractedInnovation(
                name=prompt.split("Title: ")[1].split("\n")[0][:30]
                if "Title: " in prompt
                else "Innovation",
                category=QECategory.EXECUTION_AND_OPTIMIZATION,
                evidence_tier=tier,
                key_innovation="Extracted key technical advance from benchmark payload.",
                technical_claims=["High-order fault detection verified"],
                has_reproducible_benchmark=has_bench,
                has_open_source_repo=has_repo,
                is_superficial_wrapper=is_wrapper,
            )
            return res  # type: ignore[return-value]

        return await super().generate_structured(prompt, response_model, system_prompt)


@pytest.fixture
def golden_data() -> dict[str, list[dict[str, object]]]:
    path = Path("data/fixtures/golden_benchmark.json")
    assert path.exists(), f"Golden benchmark fixture missing at {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data  # type: ignore[no-any-return]


@pytest.mark.asyncio
async def test_golden_benchmark_genuine_innovations_100_percent_recall(
    golden_data: dict[str, list[dict[str, object]]],
) -> None:
    provider = DeterministicBenchmarkProvider()
    sieve = NoiseSieve()
    extractor = DeepExtractor(provider=provider)
    convergence = TopicConvergenceEngine(provider=provider)
    evaluator = MultiLensEvaluator(provider=provider)
    categorizer = RadarCategorizer()

    genuine_list = golden_data["genuine_innovations"]
    assert len(genuine_list) == 10

    published_items: list[RadarItem] = []

    for item_data in genuine_list:
        meta_val = item_data.get("metadata")
        meta_dict: dict[str, Any] = meta_val if isinstance(meta_val, dict) else {}
        eng_val = item_data.get("engagement_metrics")
        eng_dict: dict[str, float] = eng_val if isinstance(eng_val, dict) else {}

        payload = SourcePayload(
            id=UUID(str(item_data["id"])),
            source_type=SourceType(str(item_data["source_type"])),
            source_url=str(item_data["source_url"]),
            title=str(item_data["title"]),
            raw_content=str(item_data["raw_content"]),
            author=str(item_data.get("author", "")),
            metadata=meta_dict,
            engagement_metrics=eng_dict,
        )

        # Stage 1: Noise Sieve
        sieve_res, qualified = sieve.evaluate(payload)
        assert sieve_res.passed is True, f"Genuine innovation dropped by Stage 1: {payload.title}"
        assert qualified is not None

        # Stage 2: Deep Extractor
        dossier = await extractor.extract(qualified)
        assert dossier.id is not None

        # Stage 3: Topic Convergence & Multi-Lens Committee
        conv_res = await convergence.converge_dossier(dossier)
        topic = convergence.get_topic(conv_res.topic_id)
        evaluation = await evaluator.evaluate(dossier, topic=topic)

        # Stage 4: Radar Categorizer
        radar_item = categorizer.categorize(dossier, evaluation, topic=topic)
        published_items.append(radar_item)

        # Assert Genuine Acceptance Gates
        assert radar_item.recommended_ring in (
            RadarRing.ADOPT,
            RadarRing.TRIAL,
            RadarRing.ASSESS,
        ), (
            f"Genuine innovation ended in HOLD: {radar_item.name} (viability={radar_item.viability_score}, hype={radar_item.hype_score})"
        )
        assert 0.0 <= radar_item.hype_score <= 0.50

    assert len(published_items) == 10


@pytest.mark.asyncio
async def test_golden_benchmark_hype_products_zero_leakage(
    golden_data: dict[str, list[dict[str, object]]],
) -> None:
    provider = DeterministicBenchmarkProvider()
    sieve = NoiseSieve()
    extractor = DeepExtractor(provider=provider)
    convergence = TopicConvergenceEngine(provider=provider)
    evaluator = MultiLensEvaluator(provider=provider)
    categorizer = RadarCategorizer()

    hype_list = golden_data["hype_products"]
    assert len(hype_list) == 10

    dropped_at_stage_1 = 0
    held_at_stage_4 = 0

    for item_data in hype_list:
        meta_val = item_data.get("metadata")
        meta_dict: dict[str, Any] = meta_val if isinstance(meta_val, dict) else {}
        eng_val = item_data.get("engagement_metrics")
        eng_dict: dict[str, float] = eng_val if isinstance(eng_val, dict) else {}

        payload = SourcePayload(
            id=UUID(str(item_data["id"])),
            source_type=SourceType(str(item_data["source_type"])),
            source_url=str(item_data["source_url"]),
            title=str(item_data["title"]),
            raw_content=str(item_data["raw_content"]),
            author=str(item_data.get("author", "")),
            metadata=meta_dict,
            engagement_metrics=eng_dict,
        )

        # Stage 1: Noise Sieve
        sieve_res, qualified = sieve.evaluate(payload)
        if not sieve_res.passed:
            dropped_at_stage_1 += 1
            continue

        # If it bypassed Stage 1 (e.g. subtle wrapper without keyword spam),
        # verify that downstream Stages 2, 3, 4 properly catch and quarantine it into HOLD
        assert qualified is not None
        dossier = await extractor.extract(qualified)
        conv_res = await convergence.converge_dossier(dossier)
        topic = convergence.get_topic(conv_res.topic_id)
        evaluation = await evaluator.evaluate(dossier, topic=topic)
        radar_item = categorizer.categorize(dossier, evaluation, topic=topic)

        # Must be assigned to HOLD
        assert radar_item.recommended_ring == RadarRing.HOLD, (
            f"Hype product leaked into active rings: {radar_item.name} ({radar_item.recommended_ring.value})"
        )
        assert radar_item.recommended_ring not in (
            RadarRing.ADOPT,
            RadarRing.TRIAL,
            RadarRing.ASSESS,
        )
        held_at_stage_4 += 1

    total_quarantined = dropped_at_stage_1 + held_at_stage_4
    assert total_quarantined == 10, (
        f"Expected 10/10 hype products quarantined, got {total_quarantined}"
    )
    assert dropped_at_stage_1 >= 7, (
        f"Expected >= 7 dropped at Stage 1 perimeter, got {dropped_at_stage_1}"
    )
