"""Unit tests for WatermarkManager and incremental sync state."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from radar.core.watermark import DEFAULT_INITIAL_LOOKBACK_DAYS, SyncState, WatermarkManager


def test_watermark_manager_fresh_initialization(tmp_path: Path) -> None:
    state_file = tmp_path / ".sync_state.json"
    manager = WatermarkManager(state_path=state_file)

    assert manager.state.last_sync_at is None
    assert len(manager.state.sources) == 0

    # Default lookback for unknown source is ~365 days ago
    watermark = manager.get_watermark("arxiv-cs-se")
    expected = datetime.now(UTC) - timedelta(days=DEFAULT_INITIAL_LOOKBACK_DAYS)
    assert abs((watermark - expected).total_seconds()) < 5


def test_watermark_manager_update_and_persist(tmp_path: Path) -> None:
    state_file = tmp_path / ".sync_state.json"
    manager = WatermarkManager(state_path=state_file)

    sync_time = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)
    manager.update_source_watermark("github-test-gen", sync_time)
    manager.record_sync_completion(
        ingested_count=10,
        qualified_count=5,
        evaluated_count=4,
        completed_at=sync_time,
    )

    assert state_file.exists()

    # Re-read from disk with a new manager instance
    reloaded = WatermarkManager(state_path=state_file)
    assert reloaded.state.last_sync_at == sync_time
    assert reloaded.get_watermark("github-test-gen") == sync_time
    assert len(reloaded.state.history) == 1
    assert reloaded.state.history[0].ingested_count == 10
    assert reloaded.state.history[0].evaluated_count == 4


def test_watermark_manager_reset_all_and_single_source(tmp_path: Path) -> None:
    state_file = tmp_path / ".sync_state.json"
    manager = WatermarkManager(state_path=state_file)

    now = datetime.now(UTC)
    manager.update_source_watermark("src-1", now)
    manager.update_source_watermark("src-2", now)
    manager.save()

    # Reset single source
    manager.reset_source("src-1", lookback_days=30)
    expected_30d = now - timedelta(days=30)
    assert abs((manager.get_watermark("src-1") - expected_30d).total_seconds()) < 5
    assert manager.get_watermark("src-2") == now

    # Reset all
    manager.reset_all(lookback_days=365)
    expected_365d = now - timedelta(days=365)
    assert abs((manager.get_watermark("src-1") - expected_365d).total_seconds()) < 5
    assert abs((manager.get_watermark("src-2") - expected_365d).total_seconds()) < 5
    assert manager.state.last_sync_at is None


def test_watermark_manager_corrupted_file_recovery(tmp_path: Path) -> None:
    state_file = tmp_path / ".sync_state.json"
    state_file.write_text("{ this is not valid json", encoding="utf-8")

    manager = WatermarkManager(state_path=state_file)
    assert isinstance(manager.state, SyncState)
    assert manager.state.last_sync_at is None
