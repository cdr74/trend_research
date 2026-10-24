"""Radar Command Line Interface."""

import asyncio

import click
from rich.console import Console
from rich.table import Table

from radar.core.models import SourcePayload
from radar.ingestion.arxiv import ArxivIngestor

console = Console()


async def _run_ingest(
    sources: str,
    limit: int,
    query: str | None,
    save: bool,
    ingestor_override: ArxivIngestor | None = None,
) -> list[SourcePayload]:
    """Execute asynchronous signal ingestion across requested channels."""
    source_list = [s.strip().lower() for s in sources.split(",") if s.strip()]
    console.print(
        f"[bold green]Starting ingestion from:[/bold green] {', '.join(source_list)} (limit={limit})"
    )

    records: list[SourcePayload] = []
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

    table = Table(
        title="Ingested Raw Signals",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Channel", style="dim", width=8)
    table.add_column("ID", width=12)
    table.add_column("Title", style="bold", width=42)
    table.add_column("Authors", width=22)
    table.add_column("Published", width=12)
    table.add_column("Velocity", justify="right", width=10)

    for r in records:
        pub_str = r.published_date.strftime("%Y-%m-%d") if r.published_date else "N/A"
        arxiv_id = str(r.metadata.get("arxiv_id", ""))
        velocity = r.engagement_metrics.get("velocity", 0.0)
        table.add_row(
            r.source_type.value,
            arxiv_id,
            r.title[:40] + "..." if len(r.title) > 40 else r.title,
            (r.author or "Unknown")[:20],
            pub_str,
            f"{velocity:.2f}",
        )

    console.print(table)
    console.print(f"[bold green]Successfully retrieved {len(records)} signal(s).[/bold green]")

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
