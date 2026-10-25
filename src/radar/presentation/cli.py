"""Radar Command Line Interface."""

import asyncio
import csv
import json
from pathlib import Path
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
from radar.ingestion.arxiv import ArxivIngestor
from radar.ingestion.github import GithubIngestor
from radar.ingestion.rss import RssFeedIngestor
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


async def _run_evaluate(
    batch_size: int,
    mock: bool,
    provider_override: LLMProvider | None = None,
    signals_override: list[SourcePayload] | None = None,
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

    if signals_override is not None:
        records_to_evaluate = signals_override
    else:
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
    except Exception:
        # DB optional for offline/dry-run execution
        pass

    return dossiers


async def _run_query(
    ring: str | None,
    category: str | None,
    min_viability: float,
    max_hype: float,
) -> None:
    """Query active radar items from database."""
    console.print(
        f"[bold cyan]Querying radar:[/bold cyan] ring={ring}, category={category}, min_viability={min_viability}, max_hype={max_hype}"
    )
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

        table = Table(
            title=f"Radar Query Results ({len(items)} items)",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Ring", style="bold", justify="center", width=8)
        table.add_column("Technology", style="bold", width=22)
        table.add_column("QE Pillar", style="cyan", width=24)
        table.add_column("Trajectory", justify="center", width=12)
        table.add_column("Viability", justify="right", width=9)
        table.add_column("Hype", justify="right", width=7)
        table.add_column("Key Innovation", style="dim", width=40)

        for it in items:
            table.add_row(
                it.recommended_ring,
                it.name[:20],
                it.category,
                it.lifecycle_stage,
                f"{it.viability_score:.2f}",
                f"{it.hype_score:.2f}",
                (it.key_innovation[:38] + "...")
                if len(it.key_innovation) > 38
                else it.key_innovation,
            )
        console.print(table)
    except Exception as e:
        console.print(f"[yellow]Could not execute query (DB running?): {e}[/yellow]")


async def _run_export(export_format: str, output: str) -> None:
    """Export radar items to JSON or CSV."""
    console.print(
        f"[bold magenta]Exporting radar data to:[/bold magenta] {output} ({export_format})"
    )
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from radar.db.repository import RadarRepository
        from radar.db.session import get_db_session

        async with get_db_session() as session:
            repo = RadarRepository(session)
            db_items = await repo.query_radar_items()
    except Exception as e:
        console.print(f"[yellow]Could not fetch records from database: {e}[/yellow]")
        db_items = []

    data = [
        {
            "id": str(it.id),
            "name": it.name,
            "category": it.category,
            "source_url": it.source_url,
            "evidence_tier": it.evidence_tier,
            "recommended_ring": it.recommended_ring,
            "lifecycle_stage": it.lifecycle_stage,
            "viability_score": it.viability_score,
            "hype_score": it.hype_score,
            "corroboration_count": it.corroboration_count,
            "key_innovation": it.key_innovation,
            "enterprise_risks": it.enterprise_risks,
            "prerequisites": it.prerequisites,
        }
        for it in db_items
    ]

    if export_format == "json":
        out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    elif export_format == "csv":
        if data:
            fieldnames = list(data[0].keys())
            with out_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
        else:
            out_path.write_text("", encoding="utf-8")

    console.print(f"[bold green]Exported {len(data)} items to {out_path}[/bold green]")


async def _run_inspect(item_id: str, mock: bool = False) -> None:
    """Inspect detailed evaluation dossier, critiques, and risks for an item."""
    console.print(f"[bold cyan]Inspecting radar item:[/bold cyan] {item_id}")
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
        if mock:
            console.print(
                f"[yellow]Database offline ({e}). Generating test report with mock data...[/yellow]"
            )
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
            console.print(
                f"[bold green][MOCK] Report successfully generated at: {path}[/bold green]"
            )
        else:
            console.print(
                f"[red]Database unavailable ({e}). Cannot generate executive report offline unless --mock is specified.[/red]"
            )


@main.command()
@click.option("--batch-size", default=20, help="Number of records to evaluate.")
@click.option("--mock", is_flag=True, help="Force mock LLM provider.")
def evaluate(batch_size: int, mock: bool) -> None:
    """Run the 4-stage evaluation DAG against pending signals."""
    asyncio.run(_run_evaluate(batch_size=batch_size, mock=mock))


@main.command()
@click.option("--ring", type=click.Choice(["Adopt", "Trial", "Assess", "Hold"]))
@click.option("--category", help="Filter by QE category pillar.")
@click.option("--min-viability", type=float, default=0.0)
@click.option("--max-hype", type=float, default=1.0)
def query(
    ring: str | None,
    category: str | None,
    min_viability: float,
    max_hype: float,
) -> None:
    """Query evaluated radar signals."""
    asyncio.run(
        _run_query(
            ring=ring,
            category=category,
            min_viability=min_viability,
            max_hype=max_hype,
        )
    )


@main.command()
@click.option("--id", "item_id", required=True, help="UUID of the radar item to inspect.")
@click.option("--mock", is_flag=True, help="Display mock inspection if database is offline.")
def inspect(item_id: str, mock: bool) -> None:
    """Inspect detailed evaluation dossier, critiques, and risks for an item."""
    asyncio.run(_run_inspect(item_id=item_id, mock=mock))


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
def export(export_format: str, output: str) -> None:
    """Export evaluated signals to static distribution files."""
    asyncio.run(_run_export(export_format=export_format, output=output))


if __name__ == "__main__":
    main()
