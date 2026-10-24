"""Radar Command Line Interface."""

import asyncio

import click
from rich.console import Console
from rich.table import Table

from radar.core.models import SourcePayload, SourceType
from radar.ingestion.arxiv import ArxivIngestor
from radar.ingestion.github import GithubIngestor
from radar.ingestion.rss import RssFeedIngestor
from radar.pipeline.noise_sieve import NoiseSieve

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


@main.command()
@click.option("--batch-size", default=20, help="Number of records to evaluate.")
@click.option("--mock", is_flag=True, help="Force mock LLM provider.")
def evaluate(batch_size: int, mock: bool) -> None:
    """Run the 4-stage evaluation DAG against pending signals."""
    console.print(
        f"[bold blue]Evaluating signals[/bold blue] (batch_size={batch_size}, mock={mock})"
    )


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
