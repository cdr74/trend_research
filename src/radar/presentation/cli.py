"""Radar Command Line Interface."""

import asyncio

import click
from rich.console import Console
from rich.table import Table

from radar.core.config import LLMProviderType
from radar.core.models import QualifiedSignal, SignalDossier, SourcePayload, SourceType
from radar.ingestion.arxiv import ArxivIngestor
from radar.ingestion.github import GithubIngestor
from radar.ingestion.rss import RssFeedIngestor
from radar.pipeline.convergence import TopicConvergenceEngine
from radar.pipeline.extractor import DeepExtractor
from radar.pipeline.noise_sieve import NoiseSieve
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

    try:
        from radar.db.repository import RadarRepository
        from radar.db.session import get_db_session

        async with get_db_session() as session:
            repo = RadarRepository(session)
            for t in topics:
                await repo.save_topic(t)
            for d in dossiers:
                await repo.save_dossier(d)
        console.print(
            f"[bold green]Persisted {len(topics)} topic(s) and {len(dossiers)} dossier(s) to PostgreSQL.[/bold green]"
        )
    except Exception:
        # DB optional for offline/dry-run execution
        pass

    return dossiers


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
    console.print(
        f"[bold cyan]Querying radar:[/bold cyan] ring={ring}, category={category}, min_viability={min_viability}, max_hype={max_hype}"
    )


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
    console.print(
        f"[bold magenta]Exporting radar data to:[/bold magenta] {output} ({export_format})"
    )


if __name__ == "__main__":
    main()
