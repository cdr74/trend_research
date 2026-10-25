"""Unit tests for the Markdown Executive Digest Generator."""

from pathlib import Path
from uuid import uuid4

import pytest

from radar.core.models import (
    EnterpriseEvaluation,
    EvidenceTier,
    LifecycleStage,
    QECategory,
    RadarItem,
    RadarRing,
    TrendTopic,
)
from radar.presentation.report import MarkdownReportGenerator


@pytest.fixture
def sample_radar_items() -> list[RadarItem]:
    return [
        RadarItem(
            id=uuid4(),
            name="AutoMut-ADS",
            category=QECategory.EXECUTION_AND_OPTIMIZATION,
            source_url="https://arxiv.org/abs/2410.18021",
            evidence_tier=EvidenceTier.ACADEMIC_PEER_REVIEWED,
            hype_score=0.15,
            viability_score=0.88,
            validity_score=0.85,
            recommended_ring=RadarRing.ADOPT,
            lifecycle_stage=LifecycleStage.CONSOLIDATED,
            corroboration_count=3,
            velocity_score=28.5,
            corroborating_sources=[
                "https://arxiv.org/abs/2410.18021",
                "https://github.com/org/repo",
            ],
            key_innovation="Automated mutation synthesis optimizing test coverage on sensor perception loops.",
            enterprise_risks=[],
            prerequisites=["Local GPU runner for CARLA simulation"],
        ),
        RadarItem(
            id=uuid4(),
            name="Playwright Headless",
            category=QECategory.TEST_SYNTHESIS,
            source_url="https://github.com/microsoft/playwright",
            evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
            hype_score=0.25,
            viability_score=0.78,
            validity_score=0.75,
            recommended_ring=RadarRing.TRIAL,
            lifecycle_stage=LifecycleStage.EMERGING,
            corroboration_count=1,
            velocity_score=45.0,
            corroborating_sources=["https://github.com/microsoft/playwright"],
            key_innovation="Reliable end-to-end browser testing automation.",
            enterprise_risks=["Browser binary size on CI worker"],
            prerequisites=["Node.js runtime environment"],
        ),
        RadarItem(
            id=uuid4(),
            name="Parasitic Wrapper AI",
            category=QECategory.TEST_SYNTHESIS,
            source_url="https://vendor.com/wrapper",
            evidence_tier=EvidenceTier.VENDOR_ANNOUNCEMENT,
            hype_score=0.85,
            viability_score=0.30,
            validity_score=0.15,
            recommended_ring=RadarRing.HOLD,
            lifecycle_stage=LifecycleStage.FADING,
            corroboration_count=1,
            velocity_score=1.0,
            corroborating_sources=["https://vendor.com/wrapper"],
            key_innovation="Repackaged GPT-4 prompt with marketing buzzwords.",
            enterprise_risks=["Data egress to third-party endpoints", "Superficial wrapper"],
            prerequisites=[],
        ),
    ]


@pytest.fixture
def sample_topics() -> list[TrendTopic]:
    return [
        TrendTopic(
            id=uuid4(),
            name="Perception Mutation Testing",
            category=QECategory.EXECUTION_AND_OPTIMIZATION,
            summary="Automated mutation synthesis and clustering for autonomous perception loops.",
            corroboration_count=3,
            sources=["https://arxiv.org/abs/2410.18021", "https://github.com/org/repo"],
            average_viability=0.88,
            average_validity=0.85,
            lifecycle_stage=LifecycleStage.CONSOLIDATED,
        )
    ]


@pytest.fixture
def sample_evaluations() -> list[EnterpriseEvaluation]:
    dossier_id = uuid4()
    return [
        EnterpriseEvaluation(
            dossier_id=dossier_id,
            security_score=0.90,
            cicd_score=0.85,
            qe_score=0.90,
            composite_viability_score=0.88,
            enterprise_risks=["Local GPU required"],
            prerequisites=["High memory runner"],
            skeptic_critique="Meets tier-1 enterprise banking constraints.",
        )
    ]


def test_markdown_report_generation(
    sample_radar_items: list[RadarItem],
    sample_topics: list[TrendTopic],
    sample_evaluations: list[EnterpriseEvaluation],
) -> None:
    generator = MarkdownReportGenerator()
    report = generator.generate_markdown(
        items=sample_radar_items,
        topics=sample_topics,
        evaluations=sample_evaluations,
        title="Executive Trend Intelligence Digest",
    )

    assert isinstance(report, str)
    assert "# Executive Trend Intelligence Digest" in report
    assert "## 1. Executive Summary & Ring Distribution" in report
    assert "AutoMut-ADS" in report
    assert "Playwright Headless" in report
    assert "Parasitic Wrapper AI" in report
    assert "Perception Mutation Testing" in report
    assert "Local GPU required" in report
    assert "ADOPT" in report
    assert "TRIAL" in report
    assert "HOLD" in report


def test_markdown_report_empty_corpus() -> None:
    generator = MarkdownReportGenerator()
    report = generator.generate_markdown(items=[])
    assert "No evaluated radar items available" in report


def test_markdown_report_write_to_file(tmp_path: Path, sample_radar_items: list[RadarItem]) -> None:
    generator = MarkdownReportGenerator()
    out_file = tmp_path / "reports" / "sub" / "digest-2026-10.md"
    written_path = generator.generate_and_save(
        items=sample_radar_items,
        output_path=out_file,
    )

    assert written_path.exists()
    content = written_path.read_text(encoding="utf-8")
    assert "AutoMut-ADS" in content
