"""Radar Command Line Interface."""

import asyncio
import csv
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from radar.core.config import LLMProviderType
from radar.core.models import (
    QECategory,
    QualifiedSignal,
    RadarItem,
    RadarRing,
    SignalDossier,
    SourcePayload,
    SourceType,
)
from radar.core.watermark import DEFAULT_INITIAL_LOOKBACK_DAYS, WatermarkManager
from radar.ingestion.arxiv import ArxivIngestor
from radar.ingestion.github import GithubIngestor
from radar.ingestion.rss import RssFeedIngestor
from radar.ingestion.sources import load_source_catalog
from radar.pipeline.categorizer import RadarCategorizer
from radar.pipeline.convergence import TopicConvergenceEngine
from radar.pipeline.evaluator import MultiLensEvaluator
from radar.pipeline.extractor import DeepExtractor
from radar.pipeline.noise_sieve import NoiseSieve
from radar.presentation.report import MarkdownReportGenerator
from radar.providers import LLMProvider, get_llm_provider

console = Console()


async def _run_ingest(
    sources: str,
    limit: int,
    query: str | None,
    save: bool,
    ingestor_override: ArxivIngestor | None = None,
    github_override: GithubIngestor | None = None,
    rss_override: RssFeedIngestor | None = None,
) -> list[SourcePayload]:
    """Execute asynchronous signal ingestion across requested channels."""
    source_list = [s.strip().lower() for s in sources.split(",") if s.strip()]
    console.print(
        f"[bold green]Starting ingestion from:[/bold green] {', '.join(source_list)} (limit={limit})"
    )

    records: list[SourcePayload] = []

    # 1. arXiv Channel
    if "arxiv" in source_list:
        search_q = query or "cat:cs.SE"
        console.print(f"[cyan]Connecting to arXiv public Atom API (query: '{search_q}')...[/cyan]")
        ingestor = ingestor_override or ArxivIngestor(search_query=search_q)

        is_healthy = await ingestor.check_health()
        if not is_healthy:
            console.print(
                "[yellow]Warning: arXiv health check failed or endpoint is unreachable.[/yellow]"
            )
        else:
            console.print("[green]arXiv endpoint healthy.[/green]")

        async for payload in ingestor.fetch_records(limit=limit):
            records.append(payload)

    # 2. GitHub Channel
    if "github" in source_list:
        gh_query = query or "topic:test-generation sort:updated"
        console.print(f"[cyan]Connecting to GitHub Search API (query: '{gh_query}')...[/cyan]")
        gh_ingestor = github_override or GithubIngestor(search_query=gh_query)

        is_healthy = await gh_ingestor.check_health()
        if not is_healthy:
            console.print(
                "[yellow]Warning: GitHub health check failed or rate limit reached.[/yellow]"
            )
        else:
            console.print("[green]GitHub endpoint healthy.[/green]")

        async for payload in gh_ingestor.fetch_records(limit=limit):
            records.append(payload)

    # 3. RSS / Practitioner Channel
    if "rss" in source_list:
        rss_url = query or "https://netflixtechblog.com/feed"
        console.print(f"[cyan]Connecting to RSS/Atom publication feed ({rss_url})...[/cyan]")
        rss_ingestor = rss_override or RssFeedIngestor(endpoint_url=rss_url)

        is_healthy = await rss_ingestor.check_health()
        if not is_healthy:
            console.print(
                "[yellow]Warning: RSS feed health check failed or endpoint unreachable.[/yellow]"
            )
        else:
            console.print("[green]RSS feed endpoint healthy.[/green]")

        async for payload in rss_ingestor.fetch_records(limit=limit):
            records.append(payload)

    sieve = NoiseSieve()

    table = Table(
        title="Ingested Raw Signals & Stage 1 Sieve Verdict",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Channel", style="dim", width=8)
    table.add_column("ID / Slug", width=14)
    table.add_column("Title", style="bold", width=36)
    table.add_column("Authors", width=16)
    table.add_column("Published", width=11)
    table.add_column("Velocity", justify="right", width=9)
    table.add_column("Noise", justify="right", width=7)
    table.add_column("Sieve", justify="center", width=7)

    passed_count = 0
    for r in records:
        pub_str = r.published_date.strftime("%Y-%m-%d") if r.published_date else "N/A"
        if r.source_type == SourceType.ARXIV:
            item_id = str(r.metadata.get("arxiv_id", ""))
            auth_wt = 1.3
        elif r.source_type == SourceType.GITHUB:
            item_id = str(r.metadata.get("repo_name", ""))
            auth_wt = 1.1
        else:
            item_id = str(r.metadata.get("feed_format", "rss"))
            auth_wt = 1.25

        velocity = r.engagement_metrics.get("velocity", 0.0)
        sieve_result, _ = sieve.evaluate(r, authority_weight=auth_wt)
        if sieve_result.passed:
            passed_count += 1
            sieve_badge = "[green]PASS[/green]"
        else:
            sieve_badge = "[red]DROP[/red]"

        table.add_row(
            r.source_type.value,
            item_id[:14],
            r.title[:34] + "..." if len(r.title) > 34 else r.title,
            (r.author or "Unknown")[:15],
            pub_str,
            f"{velocity:.2f}",
            f"{sieve_result.noise_score:.2f}",
            sieve_badge,
        )

    console.print(table)
    console.print(
        f"[bold green]Retrieved {len(records)} signal(s).[/bold green] "
        f"[bold cyan]Stage 1 Sieve Qualified:[/bold cyan] {passed_count}/{len(records)} signals."
    )
    if passed_count < len(records):
        console.print(
            f"[yellow]Stage 1 Sieve dropped {len(records) - passed_count} signal(s) exceeding hype threshold (> 0.60).[/yellow]"
        )

    if save and records:
        try:
            from radar.db.repository import RadarRepository
            from radar.db.session import get_db_session

            async with get_db_session() as session:
                repo = RadarRepository(session)
                for r in records:
                    await repo.save_source_payload(r)
            console.print(
                f"[bold green]Persisted {len(records)} signal(s) to PostgreSQL.[/bold green]"
            )
        except Exception as e:
            console.print(
                f"[yellow]Could not persist to database (is Podman DB running?): {e}[/yellow]"
            )

    return records


@click.group()
@click.version_option(package_name="radar")
def main() -> None:
    """AI Test Engineering Horizon Radar CLI."""


@main.command()
@click.option(
    "--sources",
    default="arxiv",
    help="Comma-separated ingestion sources to pull (e.g. arxiv,github,rss).",
)
@click.option(
    "--limit",
    default=5,
    type=int,
    help="Maximum number of records to pull per source.",
)
@click.option(
    "--query",
    default=None,
    type=str,
    help="Optional search query override (e.g. cat:cs.SE).",
)
@click.option(
    "--save",
    is_flag=True,
    help="Persist ingested signals to PostgreSQL database.",
)
def ingest(sources: str, limit: int, query: str | None, save: bool) -> None:
    """Ingest new signals from configured channels."""
    asyncio.run(_run_ingest(sources=sources, limit=limit, query=query, save=save))


def _prompt_start_db() -> bool:
    """Prompt user for consent to start local PostgreSQL container if offline."""
    from rich.prompt import Confirm

    console.print(
        "[bold yellow]Notice: PostgreSQL database (radar-postgres) is not running on localhost:5432.[/bold yellow]"
    )
    return Confirm.ask(
        "Would you like to start it now via 'podman compose up -d'?",
        default=True,
    )


async def _ensure_db_ready(
    auto_start: bool = False,
    no_db: bool = False,
    mock: bool = False,
) -> bool:
    """Check database availability and prompt user for container startup if offline."""
    if no_db or mock:
        return False
    from radar.db.container import ensure_db_running

    return await ensure_db_running(
        auto_start=auto_start,
        prompt_fn=_prompt_start_db,
    )


async def _run_evaluate(
    batch_size: int,
    mock: bool,
    provider_override: LLMProvider | None = None,
    signals_override: list[SourcePayload] | None = None,
    auto_start_db: bool = False,
    no_db: bool = False,
    db_available: bool | None = None,
) -> list[SignalDossier]:
    """Execute Stage 1 Sieve and Stage 2 Deep Extractor against pending signals."""
    console.print(
        f"[bold blue]Evaluating signals[/bold blue] (batch_size={batch_size}, mock={mock})"
    )
    if provider_override:
        provider = provider_override
    elif mock:
        provider = get_llm_provider(LLMProviderType.MOCK)
    else:
        provider = get_llm_provider()

    records_to_evaluate: list[SourcePayload] = []

    if db_available is None:
        db_ready = await _ensure_db_ready(auto_start=auto_start_db, no_db=no_db, mock=mock)
    else:
        db_ready = db_available

    if signals_override is not None:
        records_to_evaluate = signals_override
    elif db_ready:
        try:
            from radar.db.repository import RadarRepository
            from radar.db.session import get_db_session

            async with get_db_session() as session:
                repo = RadarRepository(session)
                db_sources = await repo.get_pending_sources(limit=batch_size)
                for db_s in db_sources:
                    records_to_evaluate.append(
                        SourcePayload(
                            id=db_s.id,
                            source_type=SourceType(db_s.source_type),
                            source_url=db_s.source_url,
                            title=db_s.title,
                            raw_content=db_s.raw_content,
                            author=db_s.author,
                            published_date=db_s.published_date,
                            ingested_at=db_s.ingested_at,
                            metadata=db_s.meta,
                            engagement_metrics=db_s.engagement_metrics,
                        )
                    )
        except Exception as e:
            console.print(f"[yellow]Could not query database for pending signals: {e}[/yellow]")

    if not records_to_evaluate:
        console.print("[dim]No pending signals found to evaluate.[/dim]")
        return []

    sieve = NoiseSieve()
    extractor = DeepExtractor(provider=provider)
    qualified_signals: list[QualifiedSignal] = []

    for r in records_to_evaluate:
        _, qualified = sieve.evaluate(r)
        if qualified:
            qualified_signals.append(qualified)

    if not qualified_signals:
        console.print("[yellow]All pending signals dropped by Stage 1 Noise Sieve.[/yellow]")
        return []

    console.print(
        f"[cyan]Running Stage 2 Deep Extractor on {len(qualified_signals)} qualified signal(s)...[/cyan]"
    )
    dossiers = await extractor.extract_batch(qualified_signals)

    table = Table(
        title="Stage 2 Extracted Innovation Dossiers",
        show_header=True,
        header_style="bold green",
    )
    table.add_column("Canonical Name", style="bold", width=22)
    table.add_column("QE Pillar", style="magenta", width=26)
    table.add_column("Evidence Tier", width=24)
    table.add_column("Bench", justify="center", width=7)
    table.add_column("Repo", justify="center", width=6)
    table.add_column("Wrapper", justify="center", width=8)
    table.add_column("Key Innovation", style="dim", width=40)

    for d in dossiers:
        table.add_row(
            d.name[:20],
            d.category.value,
            d.evidence_tier.value,
            "[green]YES[/green]" if d.has_reproducible_benchmark else "[dim]NO[/dim]",
            "[green]YES[/green]" if d.has_open_source_repo else "[dim]NO[/dim]",
            "[red]YES[/red]" if d.is_superficial_wrapper else "[green]NO[/green]",
            (d.key_innovation[:38] + "...") if len(d.key_innovation) > 38 else d.key_innovation,
        )

    console.print(table)
    console.print(
        f"[bold green]Successfully extracted {len(dossiers)} innovation dossier(s).[/bold green]"
    )

    # Stage 3 Topic Convergence & Wrapper Detection (Option 3B)
    console.print("[cyan]Running Stage 3 pgvector Topic Convergence & Wrapper Detection...[/cyan]")
    convergence_engine = TopicConvergenceEngine(provider=provider)
    await convergence_engine.converge_batch(dossiers)
    topics = convergence_engine.get_all_topics()

    topic_table = Table(
        title="Stage 3 Synthesized Trend Topics",
        show_header=True,
        header_style="bold cyan",
    )
    topic_table.add_column("Topic Name", style="bold", width=28)
    topic_table.add_column("QE Pillar", style="magenta", width=26)
    topic_table.add_column("Corroborations", justify="center", width=14)
    topic_table.add_column("Sources", justify="center", width=9)
    topic_table.add_column("Validity", justify="right", width=9)
    topic_table.add_column("Topic Synthesis", style="dim", width=42)

    for t in topics:
        topic_table.add_row(
            t.name[:26],
            t.category.value,
            str(t.corroboration_count),
            str(len(t.sources)),
            f"{t.average_validity:.2f}",
            (t.summary[:40] + "...") if len(t.summary) > 40 else t.summary,
        )

    console.print(topic_table)
    console.print(
        f"[bold green]Synthesized {len(topics)} convergent topic cluster(s).[/bold green]"
    )

    # Stage 3 Multi-Lens Evaluator Committee (Option 2C)
    console.print(
        "[cyan]Running Stage 3 Multi-Lens Committee (Security 35%, Operations 35%, Rigor 30%)...[/cyan]"
    )
    evaluator = MultiLensEvaluator(provider=provider)
    topic_map = {t.id: t for t in topics}
    evaluations = await evaluator.evaluate_batch(dossiers, topics=topic_map)

    eval_table = Table(
        title="Stage 3 Adversarial Committee Evaluations",
        show_header=True,
        header_style="bold yellow",
    )
    eval_table.add_column("Dossier Name", style="bold", width=24)
    eval_table.add_column("Security", justify="right", width=9)
    eval_table.add_column("Ops/CI-CD", justify="right", width=10)
    eval_table.add_column("Technical", justify="right", width=10)
    eval_table.add_column("Viability", justify="right", style="bold green", width=10)
    eval_table.add_column("Risks Count", justify="center", width=11)
    eval_table.add_column("Skeptic Critique", style="dim", width=38)

    dossier_map = {d.id: d for d in dossiers}
    for evaluation in evaluations:
        d_name = (
            dossier_map[evaluation.dossier_id].name
            if evaluation.dossier_id in dossier_map
            else str(evaluation.dossier_id)[:8]
        )
        eval_table.add_row(
            d_name[:22],
            f"{evaluation.security_score:.2f}",
            f"{evaluation.cicd_score:.2f}",
            f"{evaluation.qe_score:.2f}",
            f"{evaluation.composite_viability_score:.2f}",
            str(len(evaluation.enterprise_risks)),
            (evaluation.skeptic_critique[:36] + "...")
            if len(evaluation.skeptic_critique) > 36
            else evaluation.skeptic_critique,
        )

    console.print(eval_table)
    console.print(
        f"[bold green]Completed adversarial audit for {len(evaluations)} dossier(s).[/bold green]"
    )

    # Stage 4 Radar Categorizer & Lifecycle Trajectory (Option 4B)
    console.print("[cyan]Running Stage 4 Radar Categorizer & Lifecycle Trajectory...[/cyan]")
    categorizer = RadarCategorizer()
    radar_items = categorizer.categorize_batch(dossiers, evaluations, topics=topic_map)

    radar_table = Table(
        title="Stage 4 Tech Horizon Radar Published Items",
        show_header=True,
        header_style="bold magenta",
    )
    radar_table.add_column("Ring", style="bold", justify="center", width=8)
    radar_table.add_column("Technology", style="bold", width=22)
    radar_table.add_column("QE Pillar", style="cyan", width=24)
    radar_table.add_column("Trajectory", justify="center", width=12)
    radar_table.add_column("Viability", justify="right", width=9)
    radar_table.add_column("Hype", justify="right", width=7)
    radar_table.add_column("Corrob", justify="center", width=7)
    radar_table.add_column("Key Innovation", style="dim", width=36)

    for item in radar_items:
        ring_color = {
            "Adopt": "green",
            "Trial": "cyan",
            "Assess": "yellow",
            "Hold": "red",
        }.get(item.recommended_ring.value, "white")

        radar_table.add_row(
            f"[{ring_color}]{item.recommended_ring.value}[/{ring_color}]",
            item.name[:20],
            item.category.value,
            item.lifecycle_stage.value,
            f"{item.viability_score:.2f}",
            f"{item.hype_score:.2f}",
            str(item.corroboration_count),
            (item.key_innovation[:34] + "...")
            if len(item.key_innovation) > 34
            else item.key_innovation,
        )

    console.print(radar_table)
    console.print(
        f"[bold green]Published {len(radar_items)} item(s) to Horizon Radar.[/bold green]"
    )

    if db_ready:
        try:
            from radar.db.repository import RadarRepository
            from radar.db.session import get_db_session

            async with get_db_session() as session:
                repo = RadarRepository(session)
                for t in topics:
                    await repo.save_topic(t)
                for d in dossiers:
                    await repo.save_dossier(d)
                for evaluation in evaluations:
                    await repo.save_evaluation(evaluation)
                for item in radar_items:
                    await repo.save_radar_item(item)
            console.print(
                f"[bold green]Persisted {len(topics)} topic(s), {len(dossiers)} dossier(s), and {len(radar_items)} radar item(s) to PostgreSQL.[/bold green]"
            )
        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not persist radar evaluations to PostgreSQL: {e}[/yellow]"
            )

    return dossiers


def _get_mock_radar_items() -> list[RadarItem]:
    """Provide realistic mock radar items for offline testing, queries, and exports."""
    from radar.core.models import EvidenceTier, LifecycleStage, TrackType

    return [
        RadarItem(
            name="Playwright-Invariance-Agent",
            track=TrackType.TESTING,
            category=QECategory.TEST_SYNTHESIS,
            source_url="https://github.com/cdr74/playwright-invariance",
            evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
            hype_score=0.15,
            viability_score=0.92,
            validity_score=0.85,
            recommended_ring=RadarRing.ADOPT,
            lifecycle_stage=LifecycleStage.CONSOLIDATED,
            corroboration_count=4,
            velocity_score=82.5,
            corroborating_sources=[
                "https://arxiv.org/abs/2403.0001",
                "https://github.com/cdr74/playwright-invariance",
            ],
            key_innovation="Deterministic DOM-invariant locator synthesis with zero-egress local visual diffing.",
            enterprise_risks=["Requires local Playwright browser container runtime."],
            prerequisites=["Node.js 20+", "Docker or Podman"],
        ),
        RadarItem(
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
            corroborating_sources=["https://arxiv.org/abs/2410.18021"],
            key_innovation="Automated mutation synthesis optimizing test coverage.",
            enterprise_risks=[],
            prerequisites=["High memory CI runner"],
        ),
        RadarItem(
            name="SpecToProperty-LLM",
            category=QECategory.SPEC_AND_MODEL,
            source_url="https://github.com/cdr74/spec-property-gen",
            evidence_tier=EvidenceTier.ENGINEERING_POST_MORTEM,
            hype_score=0.28,
            viability_score=0.78,
            validity_score=0.72,
            recommended_ring=RadarRing.TRIAL,
            lifecycle_stage=LifecycleStage.EMERGING,
            corroboration_count=2,
            velocity_score=45.0,
            corroborating_sources=["https://github.com/cdr74/spec-property-gen"],
            key_innovation="OpenAPI and GraphQL schema transformation to Hypothesis property-based stateful models.",
            enterprise_risks=["Complex schema recursive models may require prompt tuning."],
            prerequisites=["Hypothesis test runner"],
        ),
        RadarItem(
            name="RCA-Tracer Agent",
            category=QECategory.TRIAGE_AND_FIX,
            source_url="https://github.com/cdr74/rca-tracer",
            evidence_tier=EvidenceTier.OPEN_SOURCE_REPO,
            hype_score=0.32,
            viability_score=0.75,
            validity_score=0.68,
            recommended_ring=RadarRing.TRIAL,
            lifecycle_stage=LifecycleStage.EMERGING,
            corroboration_count=2,
            velocity_score=38.0,
            corroborating_sources=["https://github.com/cdr74/rca-tracer"],
            key_innovation="Correlates distributed OpenTelemetry traces with flaky test failure logs to pinpoint thread races.",
            enterprise_risks=["Requires OpenTelemetry trace instrumentation."],
            prerequisites=["OpenTelemetry collector"],
        ),
        RadarItem(
            name="Multi-Agent Red-Team Explorer",
            track=TrackType.EVALUATION,
            category=QECategory.AGENT_SYSTEMS,
            source_url="https://arxiv.org/abs/2408.00002",
            evidence_tier=EvidenceTier.ACADEMIC_PEER_REVIEWED,
            hype_score=0.45,
            viability_score=0.58,
            validity_score=0.55,
            recommended_ring=RadarRing.ASSESS,
            lifecycle_stage=LifecycleStage.EMERGING,
            corroboration_count=1,
            velocity_score=52.0,
            corroborating_sources=[],
            key_innovation="Autonomous multi-agent exploration discovering unmapped edge-case API state transitions.",
            enterprise_risks=[
                "High token consumption; non-deterministic execution paths without fixed seeds."
            ],
            prerequisites=["Ollama or Gemini API"],
        ),
        RadarItem(
            name="Hype-Fix 99.9% AutoBugRepair",
            category=QECategory.TRIAGE_AND_FIX,
            source_url="https://vendor-hype-example.com/repair",
            evidence_tier=EvidenceTier.VENDOR_ANNOUNCEMENT,
            hype_score=0.85,
            viability_score=0.22,
            validity_score=0.15,
            recommended_ring=RadarRing.HOLD,
            lifecycle_stage=LifecycleStage.FADING,
            corroboration_count=1,
            velocity_score=5.0,
            corroborating_sources=[],
            key_innovation="Claims automated bug repair across any codebase; un-augmented prompt wrapper over proprietary LLM.",
            enterprise_risks=[
                "Transmits full private source code to vendor third-party endpoint.",
                "Non-deterministic code patches with zero formal verification.",
            ],
            prerequisites=["Vendor cloud subscription"],
        ),
    ]


def _filter_items_by_query_string(items: list[Any], query_string: str) -> list[Any]:
    """Filter items using token syntax (e.g. ring:Adopt viability:>0.8) and free terms."""
    terms = query_string.split()
    filtered = list(items)

    for term in terms:
        if ":" in term:
            key, val = term.split(":", 1)
            key = key.lower()
            val_clean = val.strip('"').lower()

            if key == "ring":
                filtered = [
                    it
                    for it in filtered
                    if (
                        it.recommended_ring
                        if isinstance(it.recommended_ring, str)
                        else it.recommended_ring.value
                    ).lower()
                    == val_clean
                ]
            elif key in ("track", "type"):
                filtered = [
                    it
                    for it in filtered
                    if val_clean
                    in (
                        it.track.value
                        if hasattr(getattr(it, "track", None), "value")
                        else str(getattr(it, "track", "testing"))
                    ).lower()
                ]
            elif key in ("category", "pillar"):
                filtered = [
                    it
                    for it in filtered
                    if val_clean
                    in (it.category if isinstance(it.category, str) else it.category.value).lower()
                ]
            elif key in ("tier", "evidence"):
                filtered = [
                    it
                    for it in filtered
                    if val_clean
                    in (
                        it.evidence_tier
                        if isinstance(it.evidence_tier, str)
                        else it.evidence_tier.value
                    ).lower()
                ]
            elif key == "viability":
                if val_clean.startswith(">"):
                    thresh = float(val_clean.lstrip(">="))
                    filtered = [it for it in filtered if it.viability_score >= thresh]
                elif val_clean.startswith("<"):
                    thresh = float(val_clean.lstrip("<="))
                    filtered = [it for it in filtered if it.viability_score <= thresh]
            elif key == "hype":
                if val_clean.startswith(">"):
                    thresh = float(val_clean.lstrip(">="))
                    filtered = [it for it in filtered if it.hype_score >= thresh]
                elif val_clean.startswith("<"):
                    thresh = float(val_clean.lstrip("<="))
                    filtered = [it for it in filtered if it.hype_score <= thresh]
            elif key == "risk":
                filtered = [
                    it
                    for it in filtered
                    if any(val_clean in r.lower() for r in it.enterprise_risks)
                ]
        else:
            free = term.strip('"').lower()
            filtered = [
                it
                for it in filtered
                if free in it.name.lower()
                or free in it.key_innovation.lower()
                or any(free in r.lower() for r in it.enterprise_risks)
            ]

    return filtered


async def _run_query(
    ring: str | None = None,
    category: str | None = None,
    min_viability: float = 0.0,
    max_hype: float = 1.0,
    sql: str | None = None,
    query_string: str | None = None,
    mock: bool = False,
    auto_start_db: bool = False,
    no_db: bool = False,
) -> None:
    """Query evaluated radar signals via standard filters, tokens, or ad-hoc SQL."""
    db_ready = await _ensure_db_ready(auto_start=auto_start_db, no_db=no_db, mock=mock)

    if sql:
        if not db_ready:
            console.print(
                "[red]Error: Direct SQL queries require an active PostgreSQL instance.[/red]"
            )
            return
        console.print(f"[bold cyan]Executing ad-hoc SQL query:[/bold cyan]\n[dim]{sql}[/dim]")
        try:
            from radar.db.repository import RadarRepository
            from radar.db.session import get_db_session

            async with get_db_session() as session:
                repo = RadarRepository(session)
                cols, rows = await repo.execute_raw_sql(sql)

            if not cols:
                console.print("[dim]Query executed successfully (0 rows returned or DDL).[/dim]")
                return

            table = Table(
                title=f"SQL Results ({len(rows)} row(s))",
                show_header=True,
                header_style="bold cyan",
            )
            for c in cols:
                table.add_column(c)
            for r in rows:
                table.add_row(*[str(val) for val in r])
            console.print(table)
            return
        except Exception as e:
            console.print(f"[red]Could not execute SQL query: {e}[/red]")
            return

    console.print(
        f"[bold cyan]Querying radar:[/bold cyan] query='{query_string or ''}' ring={ring}, category={category}, min_viability={min_viability}, max_hype={max_hype}"
    )
    items: list[Any] = []
    if db_ready:
        try:
            from radar.db.repository import RadarRepository
            from radar.db.session import get_db_session

            parsed_ring = RadarRing(ring) if ring else None
            parsed_cat = QECategory(category) if category else None

            async with get_db_session() as session:
                repo = RadarRepository(session)
                items = await repo.query_radar_items(
                    ring=parsed_ring,
                    category=parsed_cat,
                    min_viability=min_viability,
                    max_hype=max_hype,
                )
        except Exception as e:
            console.print(f"[yellow]Could not query database for radar items: {e}[/yellow]")

    if not items:
        if mock or not db_ready:
            console.print(
                "[dim]Database offline or query returned 0 rows. Using mock radar dataset for query...[/dim]"
            )
            items = _get_mock_radar_items()
            if ring:
                items = [
                    it
                    for it in items
                    if (
                        it.recommended_ring
                        if isinstance(it.recommended_ring, str)
                        else it.recommended_ring.value
                    )
                    == ring
                ]
            if category:
                items = [
                    it
                    for it in items
                    if (it.category if isinstance(it.category, str) else it.category.value)
                    == category
                ]
            items = [
                it
                for it in items
                if it.viability_score >= min_viability and it.hype_score <= max_hype
            ]
        else:
            console.print("[yellow]Could not execute query (PostgreSQL is offline).[/yellow]")
            return

    if query_string:
        items = _filter_items_by_query_string(items, query_string)

    table = Table(
        title=f"Radar Query Results ({len(items)} items)",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Ring", style="bold", justify="center", width=8)
    table.add_column("Track", style="green", justify="center", width=12)
    table.add_column("Technology", style="bold", width=22)
    table.add_column("QE Pillar", style="cyan", width=24)
    table.add_column("Trajectory", justify="center", width=12)
    table.add_column("Viability", justify="right", width=9)
    table.add_column("Hype", justify="right", width=7)
    table.add_column("Key Innovation", style="dim", width=40)

    for it in items:
        ring_display = (
            it.recommended_ring
            if isinstance(it.recommended_ring, str)
            else it.recommended_ring.value
        )
        track_attr = getattr(it, "track", "testing")
        track_display = str(track_attr.value if hasattr(track_attr, "value") else track_attr)
        cat_display = it.category if isinstance(it.category, str) else it.category.value
        traj_display = (
            it.lifecycle_stage if isinstance(it.lifecycle_stage, str) else it.lifecycle_stage.value
        )
        table.add_row(
            ring_display,
            track_display,
            it.name[:20],
            cat_display,
            traj_display,
            f"{it.viability_score:.2f}",
            f"{it.hype_score:.2f}",
            (it.key_innovation[:38] + "...") if len(it.key_innovation) > 38 else it.key_innovation,
        )
    console.print(table)


async def _run_export(export_format: str, output: str, mock: bool = False) -> None:
    """Export radar items to standard JSON bundle or CSV."""
    console.print(
        f"[bold magenta]Exporting radar data to:[/bold magenta] {output} ({export_format})"
    )
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    db_items: list[Any] = []
    embeddings: list[list[float]] = []

    try:
        from radar.db.repository import RadarRepository
        from radar.db.session import get_db_session

        async with get_db_session() as session:
            repo = RadarRepository(session)
            items_with_embeds = await repo.get_items_with_embeddings()
            db_items = [row[0] for row in items_with_embeds]
            embeddings = [
                row[1] if row[1] is not None else [0.0] * 1536 for row in items_with_embeds
            ]
    except Exception as e:
        if mock or not db_items:
            console.print(
                f"[yellow]Database offline ({e}). Generating export with mock radar fixtures...[/yellow]"
            )
            db_items = _get_mock_radar_items()
            embeddings = [
                [0.1 * i, 0.2 * (i % 3), 0.3 * (i % 2)] + [0.0] * 1533 for i in range(len(db_items))
            ]
        else:
            console.print(f"[yellow]Could not fetch records from database: {e}[/yellow]")

    # Compute 2D spatial coordinates via UMAP / PCA
    from radar.presentation.projection import project_embeddings_to_2d

    coords = project_embeddings_to_2d(embeddings) if embeddings else [(0.0, 0.0)] * len(db_items)

    item_dicts: list[dict[str, Any]] = []
    for i, it in enumerate(db_items):
        cx, cy = coords[i] if i < len(coords) else (0.0, 0.0)
        ring_val = (
            it.recommended_ring
            if isinstance(it.recommended_ring, str)
            else it.recommended_ring.value
        )
        cat_val = it.category if isinstance(it.category, str) else it.category.value
        tier_val = it.evidence_tier if isinstance(it.evidence_tier, str) else it.evidence_tier.value
        stage_val = (
            it.lifecycle_stage if isinstance(it.lifecycle_stage, str) else it.lifecycle_stage.value
        )

        item_dicts.append(
            {
                "id": str(it.id),
                "name": it.name,
                "category": cat_val,
                "source_url": it.source_url,
                "evidence_tier": tier_val,
                "recommended_ring": ring_val,
                "lifecycle_stage": stage_val,
                "viability_score": round(float(it.viability_score), 2),
                "hype_score": round(float(it.hype_score), 2),
                "validity_score": round(
                    float(getattr(it, "validity_score", 1.0 - it.hype_score)), 2
                ),
                "corroboration_count": it.corroboration_count,
                "velocity_score": round(float(getattr(it, "velocity_score", 0.0)), 1),
                "corroborating_sources": getattr(it, "corroborating_sources", []),
                "key_innovation": it.key_innovation,
                "enterprise_risks": it.enterprise_risks,
                "prerequisites": it.prerequisites,
                "cluster_x": cx,
                "cluster_y": cy,
            }
        )

    if export_format == "json":
        radar_bundle = {
            "radar_title": "AI Test Engineering Trend Horizon Radar",
            "generated_at": datetime.now(UTC).isoformat(),
            "rings": ["Adopt", "Trial", "Assess", "Hold"],
            "categories": [
                "Spec & Model",
                "Test Synthesis",
                "Execution & Optimization",
                "Triage & Self-Healing",
                "Agent Systems",
                "Governance & Evals",
            ],
            "items": item_dicts,
        }
        out_path.write_text(json.dumps(radar_bundle, indent=2), encoding="utf-8")
    elif export_format == "csv":
        if item_dicts:
            fieldnames = list(item_dicts[0].keys())
            with out_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(item_dicts)
        else:
            out_path.write_text("", encoding="utf-8")

    console.print(f"[bold green]Exported {len(item_dicts)} items to {out_path}[/bold green]")


async def _run_inspect(
    item_id: str,
    mock: bool = False,
    auto_start_db: bool = False,
) -> None:
    """Inspect detailed evaluation dossier, critiques, and risks for an item."""
    console.print(f"[bold cyan]Inspecting radar item:[/bold cyan] {item_id}")
    db_ready = await _ensure_db_ready(auto_start=auto_start_db, mock=mock)
    if not db_ready and not mock:
        console.print("[red]Could not query database (PostgreSQL database is offline).[/red]")
        return

    try:
        from radar.db.repository import RadarRepository
        from radar.db.session import get_db_session

        uid = UUID(item_id)
        async with get_db_session() as session:
            repo = RadarRepository(session)
            item = await repo.get_radar_item_by_id(uid)
            if not item:
                console.print(f"[yellow]Radar item with ID {item_id} not found.[/yellow]")
                return

            evaluation = (
                await repo.get_evaluation_by_id(item.evaluation_id) if item.evaluation_id else None
            )
            topic = await repo.get_topic_by_id(item.topic_id) if item.topic_id else None

        info_lines = [
            f"[bold]Name:[/bold] {item.name}",
            f"[bold]Ring:[/bold] {item.recommended_ring} | [bold]Category:[/bold] {item.category}",
            f"[bold]Trajectory:[/bold] {item.lifecycle_stage} | [bold]Velocity:[/bold] {item.velocity_score:.1f}",
            f"[bold]Scores:[/bold] Viability: {item.viability_score:.2f} | Validity: {item.validity_score:.2f} | Hype: {item.hype_score:.2f}",
            f"[bold]Evidence Tier:[/bold] {item.evidence_tier}",
            f"[bold]Source URL:[/bold] {item.source_url}",
            f"[bold]Key Innovation:[/bold] {item.key_innovation}",
        ]
        if topic:
            info_lines.append(
                f"[bold]Converged Topic:[/bold] {topic.name} (Corroborations: {topic.corroboration_count})"
            )
        if evaluation:
            info_lines.extend(
                [
                    "",
                    "[bold yellow]Adversarial Multi-Lens Scores & Critiques:[/bold yellow]",
                    f"  - Security Score ({evaluation.security_score:.2f}): {evaluation.security_critique or 'N/A'}",
                    f"  - CI/CD Score ({evaluation.cicd_score:.2f}): {evaluation.cicd_critique or 'N/A'}",
                    f"  - Technical Score ({evaluation.qe_score:.2f}): {evaluation.qe_critique or 'N/A'}",
                    f"  - Skeptic Verdict: {evaluation.skeptic_critique}",
                ]
            )
        if item.enterprise_risks:
            info_lines.extend(
                [
                    "",
                    "[bold red]Enterprise Risk Flags:[/bold red]",
                    *(f"  - ⚠️ {r}" for r in item.enterprise_risks),
                ]
            )
        if item.prerequisites:
            info_lines.extend(
                [
                    "",
                    "[bold green]Adoption Prerequisites:[/bold green]",
                    *(f"  - ✅ {p}" for p in item.prerequisites),
                ]
            )

        console.print(
            Panel("\n".join(info_lines), title=f"Radar Item Dossier: {item.name}", expand=False)
        )
    except Exception as e:
        if mock:
            console.print(f"[bold cyan][MOCK] Inspecting item {item_id}:[/bold cyan]")
            mock_text = (
                "Name: Mock-Innovation\n"
                "Ring: Adopt | Category: Execution & Optimization\n"
                "Viability: 0.88 | Hype: 0.12 | Trajectory: Consolidated\n"
                "Key Innovation: Automated mutation testing optimization."
            )
            console.print(Panel(mock_text, title=f"Radar Item: {item_id}", expand=False))
        else:
            console.print(f"[red]Could not query database (is Podman DB running?): {e}[/red]")


async def _run_report(output: str, mock: bool = False) -> None:
    """Generate executive Markdown report."""
    console.print(f"[bold magenta]Generating executive Markdown digest to:[/bold magenta] {output}")
    if mock:
        from radar.core.models import (
            EvidenceTier,
            LifecycleStage,
        )

        mock_items = [
            RadarItem(
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
                key_innovation="Automated mutation synthesis optimizing test coverage.",
                enterprise_risks=[],
                prerequisites=["High memory CI runner"],
            ),
        ]
        generator = MarkdownReportGenerator()
        path = generator.generate_and_save(items=mock_items, output_path=output)
        console.print(f"[bold green]Report successfully generated at: {path}[/bold green]")
        return

    try:
        from radar.db.repository import RadarRepository
        from radar.db.session import get_db_session

        async with get_db_session() as session:
            repo = RadarRepository(session)
            items = await repo.query_radar_items()
            topic_ids = {it.topic_id for it in items if it.topic_id}
            topics = []
            for tid in topic_ids:
                t = await repo.get_topic_by_id(tid)
                if t:
                    topics.append(t)

            eval_ids = {it.evaluation_id for it in items if it.evaluation_id}
            evaluations = []
            for eid in eval_ids:
                ev = await repo.get_evaluation_by_id(eid)
                if ev:
                    evaluations.append(ev)

        if not items:
            console.print(
                "[yellow]No evaluated radar items found in database to generate report.[/yellow]"
            )
            return

        generator = MarkdownReportGenerator()
        path = generator.generate_and_save(
            items=items,
            output_path=output,
            topics=topics,
            evaluations=evaluations,
        )
        console.print(f"[bold green]Report successfully generated at: {path}[/bold green]")
    except Exception as e:
        console.print(
            f"[red]Database unavailable ({e}). Cannot generate executive report offline unless --mock is specified.[/red]"
        )


@main.command()
@click.option("--batch-size", default=20, help="Number of records to evaluate.")
@click.option("--mock", is_flag=True, help="Force mock LLM provider.")
@click.option(
    "--auto-start-db",
    is_flag=True,
    help="Auto-start database container without prompting if offline.",
)
@click.option("--no-db", is_flag=True, help="Skip database persistence and run in offline mode.")
def evaluate(batch_size: int, mock: bool, auto_start_db: bool, no_db: bool) -> None:
    """Run the 4-stage evaluation DAG against pending signals."""
    asyncio.run(
        _run_evaluate(batch_size=batch_size, mock=mock, auto_start_db=auto_start_db, no_db=no_db)
    )


@main.command()
@click.argument("query_string", required=False)
@click.option("--ring", type=click.Choice(["Adopt", "Trial", "Assess", "Hold"]))
@click.option("--category", help="Filter by QE category pillar.")
@click.option("--min-viability", type=float, default=0.0)
@click.option("--max-hype", type=float, default=1.0)
@click.option("--sql", help="Ad-hoc SQL query string to execute against database.")
@click.option("--mock", is_flag=True, help="Query mock data fixtures if database is offline.")
@click.option(
    "--auto-start-db",
    is_flag=True,
    help="Auto-start database container without prompting if offline.",
)
def query(
    query_string: str | None,
    ring: str | None,
    category: str | None,
    min_viability: float,
    max_hype: float,
    sql: str | None,
    mock: bool,
    auto_start_db: bool,
) -> None:
    """Query evaluated radar signals using free-text, tokens, or ad-hoc SQL."""
    asyncio.run(
        _run_query(
            ring=ring,
            category=category,
            min_viability=min_viability,
            max_hype=max_hype,
            sql=sql,
            query_string=query_string,
            mock=mock,
            auto_start_db=auto_start_db,
        )
    )


@main.command()
@click.option("--id", "item_id", required=True, help="UUID of the radar item to inspect.")
@click.option("--mock", is_flag=True, help="Display mock inspection if database is offline.")
@click.option(
    "--auto-start-db",
    is_flag=True,
    help="Auto-start database container without prompting if offline.",
)
def inspect(item_id: str, mock: bool, auto_start_db: bool) -> None:
    """Inspect detailed evaluation dossier, critiques, and risks for an item."""
    asyncio.run(_run_inspect(item_id=item_id, mock=mock, auto_start_db=auto_start_db))


@main.command()
@click.option(
    "--output",
    default="reports/digest.md",
    help="Destination file path for the Markdown report.",
)
@click.option(
    "--mock",
    is_flag=True,
    help="Generate test report with mock fixture data if database is offline.",
)
def report(output: str, mock: bool) -> None:
    """Generate an executive Markdown intelligence digest."""
    asyncio.run(_run_report(output=output, mock=mock))


@main.command()
@click.option(
    "--format",
    "export_format",
    type=click.Choice(["json", "csv"]),
    default="json",
)
@click.option("--output", default="data/export/radar.json", help="Destination path.")
@click.option("--mock", is_flag=True, help="Export mock data fixtures if database is offline.")
def export(export_format: str, output: str, mock: bool) -> None:
    """Export evaluated signals to static distribution files with 2D UMAP projection."""
    asyncio.run(_run_export(export_format=export_format, output=output, mock=mock))


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a network port is accepting TCP connections."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


async def _run_ui(
    port: int = 5173,
    host: str = "localhost",
    no_open: bool = False,
    mock: bool = False,
    auto_start_db: bool = True,
    web_dir: Path | None = None,
) -> None:
    """Launch and orchestrate the Vite web dashboard."""
    base_dir = web_dir or Path("web")
    console.print(
        Panel.fit(
            f"[bold magenta]Trend Horizon Radar: Web Dashboard[/bold magenta]\n"
            f"[cyan]Target URL:[/cyan] http://{host}:{port}\n"
            f"[dim]Verifying dependencies, database, and radar dataset bundle...[/dim]",
            border_style="magenta",
        )
    )

    # 1. Verify database readiness
    db_ready = await _ensure_db_ready(auto_start=auto_start_db, mock=mock)
    if db_ready:
        console.print("[dim]✓ Database connection active and schema synchronized.[/dim]")

    # 2. Check radar data bundle
    bundle_path = base_dir / "public" / "radar.json"
    bundle_needs_update = True
    if bundle_path.exists():
        try:
            raw_data = json.loads(bundle_path.read_text(encoding="utf-8"))
            if raw_data.get("items"):
                bundle_needs_update = False
                console.print(
                    f"[dim]✓ Radar dataset bundle verified ({len(raw_data['items'])} items).[/dim]"
                )
        except Exception:
            bundle_needs_update = True

    if bundle_needs_update:
        console.print("[yellow]Notice: web/public/radar.json is empty or unpopulated.[/yellow]")
        console.print("[cyan]Exporting current radar signals from database to web bundle...[/cyan]")
        await _run_export(export_format="json", output=str(bundle_path), mock=mock)

    # 3. Check web/node_modules
    if not (base_dir / "node_modules").exists():
        console.print(
            "[cyan]Frontend dependencies not found. Installing via 'npm ci' in web/...[/cyan]"
        )
        proc = await asyncio.create_subprocess_exec(
            "npm",
            "ci",
            cwd=str(base_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, err = await proc.communicate()
        if proc.returncode != 0:
            console.print(f"[red]Failed to install frontend dependencies: {err.decode()}[/red]")
            return

    # 4. Check if dashboard server is already running
    url = f"http://{host}:{port}"
    if is_port_in_use(port, "127.0.0.1"):
        console.print(f"[bold green]✓ Web dashboard is already running at {url}[/bold green]")
        if not no_open:
            import webbrowser

            webbrowser.open(url)
        return

    # 5. Launch Vite server in foreground
    console.print(
        f"[bold green]Starting Vite server on {url}... (Press Ctrl+C to stop)[/bold green]"
    )
    if not no_open:
        import webbrowser

        asyncio.get_event_loop().call_later(1.5, lambda: webbrowser.open(url))

    dev_proc = await asyncio.create_subprocess_exec(
        "npm",
        "run",
        "dev",
        "--",
        "--port",
        str(port),
        "--host",
        host,
        cwd=str(base_dir),
    )
    try:
        await dev_proc.wait()
    except (asyncio.CancelledError, KeyboardInterrupt):
        console.print("\n[dim]Shutting down web dashboard server...[/dim]")
        dev_proc.terminate()
        await dev_proc.wait()


@main.command()
@click.option("--port", default=5173, type=int, help="Port for the web dashboard server.")
@click.option("--host", default="localhost", help="Host interface to bind.")
@click.option("--no-open", is_flag=True, help="Do not automatically open the web browser.")
@click.option("--mock", is_flag=True, help="Populate mock data if database is empty.")
@click.option(
    "--auto-start-db/--no-auto-start-db",
    default=True,
    help="Auto-start database container if offline.",
)
def ui(port: int, host: str, no_open: bool, mock: bool, auto_start_db: bool) -> None:
    """Launch the interactive Trend Horizon Radar web dashboard."""
    asyncio.run(
        _run_ui(port=port, host=host, no_open=no_open, mock=mock, auto_start_db=auto_start_db)
    )


@main.command()
@click.option("--port", default=5173, type=int, help="Port for the web dashboard server.")
@click.option("--host", default="localhost", help="Host interface to bind.")
@click.option("--no-open", is_flag=True, help="Do not automatically open the web browser.")
@click.option("--mock", is_flag=True, help="Populate mock data if database is empty.")
@click.option(
    "--auto-start-db/--no-auto-start-db",
    default=True,
    help="Auto-start database container if offline.",
)
def serve(port: int, host: str, no_open: bool, mock: bool, auto_start_db: bool) -> None:
    """Alias for 'radar ui' - launch the interactive web dashboard."""
    asyncio.run(
        _run_ui(port=port, host=host, no_open=no_open, mock=mock, auto_start_db=auto_start_db)
    )


async def _run_sync(
    days: int | None = None,
    since: str | None = None,
    reset: bool = False,
    reset_source: str | None = None,
    limit_per_source: int = 20,
    no_eval: bool = False,
    no_report: bool = False,
    no_export: bool = False,
    mock: bool = False,
    auto_start_db: bool = False,
    no_db: bool = False,
    ui: bool = False,
    state_path: Path | None = None,
    catalog_path: Path | None = None,
) -> None:
    """Execute on-demand incremental ingestion, evaluation, and dashboard refresh."""
    sync_start = datetime.now(UTC)
    manager = WatermarkManager(state_path=state_path or Path("data/.sync_state.json"))

    db_ready = await _ensure_db_ready(auto_start=auto_start_db, no_db=no_db, mock=mock)
    if db_ready:
        console.print("[dim]✓ PostgreSQL database connection active.[/dim]")
    elif not mock and not no_db:
        console.print(
            "[dim]Operating in offline mode (signals will not be persisted to PostgreSQL).[/dim]"
        )

    if reset:
        manager.reset_all(lookback_days=days or DEFAULT_INITIAL_LOOKBACK_DAYS)
        console.print(
            f"[bold yellow]Reset all source watermarks to {days or DEFAULT_INITIAL_LOOKBACK_DAYS} days lookback.[/bold yellow]"
        )

    if reset_source:
        manager.reset_source(reset_source, lookback_days=days or DEFAULT_INITIAL_LOOKBACK_DAYS)
        console.print(
            f"[bold yellow]Reset watermark for source '{reset_source}' to {days or DEFAULT_INITIAL_LOOKBACK_DAYS} days lookback.[/bold yellow]"
        )

    since_override: datetime | None = None
    if since:
        try:
            since_override = datetime.fromisoformat(since)
            if since_override.tzinfo is None:
                since_override = since_override.replace(tzinfo=UTC)
        except ValueError:
            console.print(f"[red]Invalid ISO date format for --since: '{since}'.[/red]")
            return
    elif days is not None:
        since_override = sync_start - timedelta(days=days)

    try:
        catalog = load_source_catalog(catalog_path)
        enabled_sources = catalog.get_enabled()
    except Exception as e:
        console.print(
            f"[yellow]Could not load source catalog ({e}). Falling back to baseline channels.[/yellow]"
        )
        enabled_sources = []

    console.print(
        Panel.fit(
            f"[bold magenta]Trend Horizon Radar: On-Demand Incremental Sync[/bold magenta]\n"
            f"[cyan]Active Sources:[/cyan] {len(enabled_sources)} enabled streams\n"
            f"[cyan]Default Lookback:[/cyan] {DEFAULT_INITIAL_LOOKBACK_DAYS} days (Initial Baseline)\n"
            f"[cyan]Execution Time:[/cyan] {sync_start.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            border_style="magenta",
        )
    )

    all_ingested: list[SourcePayload] = []
    sieve = NoiseSieve()
    qualified_signals: list[QualifiedSignal] = []

    if mock or not enabled_sources:
        console.print("[dim]Executing sync with deterministic mock fixtures...[/dim]")
        mock_items = _get_mock_radar_items()
        all_ingested = [
            SourcePayload(
                source_type=SourceType.GITHUB,
                source_url=it.source_url,
                title=it.name,
                raw_content=it.key_innovation,
            )
            for it in mock_items
        ]
        for p in all_ingested:
            _, qualified = sieve.evaluate(p)
            if qualified:
                qualified_signals.append(qualified)
    else:
        for src in enabled_sources:
            src_since = since_override or manager.get_watermark(
                src.id, default_lookback_days=DEFAULT_INITIAL_LOOKBACK_DAYS
            )
            console.print(
                f"[bold cyan]Syncing source stream:[/bold cyan] {src.name} ([dim]since {src_since.strftime('%Y-%m-%d')}[/dim])"
            )

            src_records: list[SourcePayload] = []
            try:
                if src.channel in ("academic", "arxiv"):
                    query = src.query_params.get("search_query", "cat:cs.SE")
                    arxiv_ingestor = ArxivIngestor(
                        search_query=query,
                        authority_weight=src.authority_weight,
                    )
                    async for payload in arxiv_ingestor.fetch_records(
                        since=src_since, limit=limit_per_source
                    ):
                        src_records.append(payload)
                elif src.channel == "github":
                    query = src.query_params.get("q", "topic:test-generation sort:updated")
                    gh_ingestor = GithubIngestor(
                        search_query=query,
                        authority_weight=src.authority_weight,
                    )
                    async for payload in gh_ingestor.fetch_records(
                        since=src_since, limit=limit_per_source
                    ):
                        src_records.append(payload)
                elif src.channel in ("rss", "community"):
                    rss_ingestor = RssFeedIngestor(
                        endpoint_url=src.endpoint_url,
                        authority_weight=src.authority_weight,
                    )
                    async for payload in rss_ingestor.fetch_records(
                        since=src_since, limit=limit_per_source
                    ):
                        src_records.append(payload)

                all_ingested.extend(src_records)
                manager.update_source_watermark(src.id, sync_start)
                console.print(f"  [green]✓ Ingested {len(src_records)} new record(s)[/green]")
            except Exception as e:
                console.print(f"  [yellow]⚠ Source {src.name} sync encountered error: {e}[/yellow]")

        # Deduplicate all_ingested in-memory by source_url
        seen_urls: set[str] = set()
        deduped: list[SourcePayload] = []
        for p in all_ingested:
            if p.source_url not in seen_urls:
                seen_urls.add(p.source_url)
                deduped.append(p)
        all_ingested = deduped

        for p in all_ingested:
            _, qualified = sieve.evaluate(p)
            if qualified:
                qualified_signals.append(qualified)

    # Persist raw payloads if DB available
    if db_ready:
        try:
            from radar.db.repository import RadarRepository
            from radar.db.session import get_db_session

            saved_count = 0
            async with get_db_session() as session:
                repo = RadarRepository(session)
                for p in all_ingested:
                    await repo.save_source_payload(p)
                    saved_count += 1
            console.print(f"  [dim]Saved/updated {saved_count} raw payload(s) in PostgreSQL.[/dim]")
        except Exception as e:
            console.print(f"  [yellow]Failed to persist payloads to PostgreSQL: {e}[/yellow]")

    evaluated_count = 0
    if not no_eval and qualified_signals:
        console.print(
            f"[bold cyan]Running 4-stage evaluation DAG on {len(qualified_signals)} qualified signals...[/bold cyan]"
        )
        dossiers = await _run_evaluate(
            batch_size=len(qualified_signals),
            mock=mock,
            signals_override=[q.payload for q in qualified_signals],
            db_available=db_ready,
        )
        evaluated_count = len(dossiers)

    if not no_export:
        console.print("[cyan]Updating static radar data bundle (web/public/radar.json)...[/cyan]")
        await _run_export(export_format="json", output="web/public/radar.json", mock=mock)

    if not no_report:
        report_path = f"reports/{sync_start.strftime('%Y-W%V')}.md"
        console.print(f"[cyan]Generating executive Markdown digest ({report_path})...[/cyan]")
        await _run_report(output=report_path, mock=mock)

    manager.record_sync_completion(
        ingested_count=len(all_ingested),
        qualified_count=len(qualified_signals),
        evaluated_count=evaluated_count,
        completed_at=sync_start,
    )

    console.print(
        f"[bold green]Sync complete! Ingested: {len(all_ingested)} | Qualified: {len(qualified_signals)} | Evaluated: {evaluated_count}[/bold green]"
    )

    dashboard_active = is_port_in_use(5173)
    if dashboard_active:
        console.print(
            "[bold green]✓ Web dashboard is live at http://localhost:5173 (data bundle updated).[/bold green]"
        )
    elif ui:
        console.print("[cyan]Launching web dashboard...[/cyan]")
        await _run_ui(port=5173, mock=mock, auto_start_db=False)
    else:
        console.print("[dim]To view the dashboard, run: uv run radar ui[/dim]")


@main.command()
@click.option(
    "--days",
    type=int,
    help="Override lookback window in days (e.g. 365 for 1-year baseline).",
)
@click.option("--since", help="Override sync start timestamp (ISO format: YYYY-MM-DD).")
@click.option(
    "--reset", is_flag=True, help="Reset all source watermarks back to baseline lookback."
)
@click.option(
    "--reset-source", help="Reset watermark for a specific source ID (from sources.yaml)."
)
@click.option("--limit-per-source", default=20, help="Maximum records to fetch per source stream.")
@click.option("--no-eval", is_flag=True, help="Skip running the 4-stage evaluation DAG.")
@click.option("--no-report", is_flag=True, help="Skip generating the executive Markdown report.")
@click.option("--no-export", is_flag=True, help="Skip exporting web/public/radar.json.")
@click.option("--ui", is_flag=True, help="Launch web dashboard upon sync completion.")
@click.option("--mock", is_flag=True, help="Execute offline sync using mock fixtures.")
@click.option(
    "--auto-start-db",
    is_flag=True,
    help="Auto-start database container without prompting if offline.",
)
@click.option(
    "--no-db",
    is_flag=True,
    help="Run in offline mode without database persistence.",
)
def sync(
    days: int | None,
    since: str | None,
    reset: bool,
    reset_source: str | None,
    limit_per_source: int,
    no_eval: bool,
    no_report: bool,
    no_export: bool,
    ui: bool,
    mock: bool,
    auto_start_db: bool,
    no_db: bool,
) -> None:
    """Synchronize trends incrementally since last run and update web radar."""
    asyncio.run(
        _run_sync(
            days=days,
            since=since,
            reset=reset,
            reset_source=reset_source,
            limit_per_source=limit_per_source,
            no_eval=no_eval,
            no_report=no_report,
            no_export=no_export,
            ui=ui,
            mock=mock,
            auto_start_db=auto_start_db,
            no_db=no_db,
        )
    )


if __name__ == "__main__":
    main()
