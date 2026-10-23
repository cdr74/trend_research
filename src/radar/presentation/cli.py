"""Radar Command Line Interface."""

import click
from rich.console import Console

console = Console()


@click.group()
@click.version_option(package_name="radar")
def main() -> None:
    """AI Test Engineering Horizon Radar CLI."""


@main.command()
@click.option(
    "--sources",
    default="arxiv,github,rss",
    help="Comma-separated ingestion sources to pull.",
)
def ingest(sources: str) -> None:
    """Ingest new signals from configured channels."""
    console.print(f"[bold green]Starting ingestion from:[/bold green] {sources}")
    # Ingestion pipeline dispatch will be linked here


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
