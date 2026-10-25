"""Unit tests for the Radar command line interface."""

import json
from pathlib import Path

import httpx
import pytest
from click.testing import CliRunner

from radar.core.models import SourcePayload, SourceType
from radar.ingestion.arxiv import ArxivIngestor
from radar.ingestion.github import GithubIngestor
from radar.ingestion.rss import RssFeedIngestor
from radar.presentation.cli import _run_evaluate, _run_ingest, main
from radar.providers.mock import MockProvider


def test_cli_version() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "radar" in result.output.lower() or "version" in result.output.lower()


def test_cli_query_and_export_commands(tmp_path: Path) -> None:
    runner = CliRunner()

    eval_res = runner.invoke(main, ["evaluate", "--batch-size", "10", "--mock"])
    assert eval_res.exit_code == 0
    assert "Evaluating signals" in eval_res.output

    query_res = runner.invoke(main, ["query", "--ring", "Adopt"])
    assert query_res.exit_code == 0
    assert "Querying radar" in query_res.output

    out_json = tmp_path / "radar.json"
    export_json_res = runner.invoke(
        main, ["export", "--format", "json", "--output", str(out_json), "--mock"]
    )
    assert export_json_res.exit_code == 0
    assert "Exporting radar data" in export_json_res.output
    assert out_json.exists()
    raw_data = json.loads(out_json.read_text(encoding="utf-8"))
    assert raw_data["radar_title"] == "AI Test Engineering Trend Horizon Radar"
    assert len(raw_data["items"]) >= 1
    assert "cluster_x" in raw_data["items"][0]
    assert "cluster_y" in raw_data["items"][0]

    out_csv = tmp_path / "radar.csv"
    export_csv_res = runner.invoke(
        main, ["export", "--format", "csv", "--output", str(out_csv), "--mock"]
    )
    assert export_csv_res.exit_code == 0
    assert "Exporting radar data" in export_csv_res.output
    assert out_csv.exists()


def test_cli_query_token_and_free_text_search() -> None:
    runner = CliRunner()

    # Query with structured token expression in mock mode
    token_res = runner.invoke(main, ["query", "ring:Adopt viability:>0.8", "--mock"])
    assert token_res.exit_code == 0
    assert "Playwright" in token_res.output
    assert "Hype-Fix" not in token_res.output

    # Query with free text keyword in mock mode
    text_res = runner.invoke(main, ["query", "deterministic", "--mock"])
    assert text_res.exit_code == 0
    assert "Playwright" in text_res.output


def test_cli_inspect_command() -> None:
    runner = CliRunner()
    res = runner.invoke(main, ["inspect", "--id", "11111111-1111-1111-1111-111111111111", "--mock"])
    assert res.exit_code == 0
    assert "Inspecting radar item" in res.output
    assert "Mock-Innovation" in res.output


def test_cli_report_command_offline_safety_and_mock(tmp_path: Path) -> None:
    runner = CliRunner()
    out_report = tmp_path / "digest.md"

    # Offline without mock: should refuse to generate report and warn user
    offline_res = runner.invoke(main, ["report", "--output", str(out_report)])
    assert (
        "Cannot generate executive report offline" in offline_res.output
        or "Database unavailable" in offline_res.output
    )
    assert not out_report.exists()

    # Offline with --mock: should generate test report
    mock_res = runner.invoke(main, ["report", "--output", str(out_report), "--mock"])
    assert mock_res.exit_code == 0
    assert "Report successfully generated" in mock_res.output
    assert out_report.exists()
    assert "AutoMut-ADS" in out_report.read_text(encoding="utf-8")


def test_cli_sync_command_mock_and_resets() -> None:
    runner = CliRunner()

    # Run sync in mock mode
    res = runner.invoke(main, ["sync", "--mock"])
    assert res.exit_code == 0
    assert "Trend Horizon Radar: On-Demand Incremental Sync" in res.output
    assert "Sync complete!" in res.output

    # Run sync with --reset
    reset_res = runner.invoke(main, ["sync", "--mock", "--reset", "--days", "365"])
    assert reset_res.exit_code == 0
    assert "Reset all source watermarks" in reset_res.output

    # Run sync with --reset-source
    reset_src_res = runner.invoke(
        main, ["sync", "--mock", "--reset-source", "github-topic-test-generation"]
    )
    assert reset_src_res.exit_code == 0
    assert "Reset watermark for source 'github-topic-test-generation'" in reset_src_res.output


@pytest.mark.asyncio
async def test_run_ingest_arxiv(sample_arxiv_xml: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(200, text=sample_arxiv_xml)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        mock_ingestor = ArxivIngestor(client=client, rate_limit_delay=0.0)
        records = await _run_ingest(
            sources="arxiv",
            limit=2,
            query="cat:cs.SE",
            save=False,
            ingestor_override=mock_ingestor,
        )
        assert len(records) == 2
        assert records[0].metadata["arxiv_id"] == "2410.18021"


def test_cli_ingest_command_invocation(
    monkeypatch: pytest.MonkeyPatch, sample_arxiv_xml: str
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(200, text=sample_arxiv_xml)

    transport = httpx.MockTransport(handler)
    real_async_client = httpx.AsyncClient

    def mock_client_factory(*_args: object, **kwargs: object) -> httpx.AsyncClient:
        kwargs["transport"] = transport
        return real_async_client(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(httpx, "AsyncClient", mock_client_factory)

    runner = CliRunner()
    result = runner.invoke(main, ["ingest", "--sources", "arxiv", "--limit", "2"])
    assert result.exit_code == 0
    assert "Automated Mutation Testing" in result.output
    assert "Retrieved 2 signal(s)" in result.output
    assert "Stage 1 Sieve Qualified" in result.output


@pytest.mark.asyncio
async def test_run_ingest_github(sample_github_response: dict[str, object]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(200, json=sample_github_response)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        mock_gh = GithubIngestor(client=client, rate_limit_delay=0.0)
        records = await _run_ingest(
            sources="github",
            limit=2,
            query="topic:test-generation",
            save=False,
            github_override=mock_gh,
        )
        assert len(records) == 2
        assert records[0].title == "microsoft/playwright"
        assert records[0].engagement_metrics["stars"] == 65000.0


@pytest.mark.asyncio
async def test_run_ingest_rss(sample_rss_xml: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(200, text=sample_rss_xml)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        mock_rss = RssFeedIngestor(client=client, rate_limit_delay=0.0)
        records = await _run_ingest(
            sources="rss",
            limit=2,
            query="https://netflixtechblog.com/feed",
            save=False,
            rss_override=mock_rss,
        )
        assert len(records) == 2
        assert records[0].title == "Chaos Engineering in the Cloud Era"


@pytest.mark.asyncio
async def test_run_evaluate_with_mock_signals() -> None:
    provider = MockProvider(embedding_dim=1536)
    genuine_payload = SourcePayload(
        source_type=SourceType.GITHUB,
        source_url="https://github.com/microsoft/playwright",
        title="microsoft/playwright",
        raw_content="Reliable end-to-end testing for modern web apps with automated headless browsers.",
    )
    hype_payload = SourcePayload(
        source_type=SourceType.RSS,
        source_url="https://hypeblog.com/post1",
        title="100x Faster Revolutionary AI Testing Replaces All Engineers",
        raw_content="100% bug-free guarantee with this miraculous silver bullet! Affiliate link inside.",
    )

    dossiers = await _run_evaluate(
        batch_size=5,
        mock=True,
        provider_override=provider,
        signals_override=[genuine_payload, hype_payload],
    )

    assert len(dossiers) == 1
    assert dossiers[0].source_id == genuine_payload.id
    assert dossiers[0].embedding is not None
    assert len(dossiers[0].embedding) == 1536
