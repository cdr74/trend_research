"""High-water mark state tracking for on-demand incremental ingestion and evaluation."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

DEFAULT_INITIAL_LOOKBACK_DAYS: int = 365
DEFAULT_STATE_PATH: Path = Path("data/.sync_state.json")


class SyncRunRecord(BaseModel):
    """Metadata recorded for an individual sync pipeline execution."""

    synced_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ingested_count: int = 0
    qualified_count: int = 0
    evaluated_count: int = 0


class SyncState(BaseModel):
    """Persistent state containing global and per-source high-water marks."""

    version: str = "1.0"
    last_sync_at: datetime | None = None
    sources: dict[str, datetime] = Field(default_factory=dict)
    history: list[SyncRunRecord] = Field(default_factory=list)


class WatermarkManager:
    """Manages reading, persisting, and resetting ingestion watermarks."""

    def __init__(self, state_path: Path | str = DEFAULT_STATE_PATH) -> None:
        self.state_path = Path(state_path)
        self.state: SyncState = self._load()

    def _load(self) -> SyncState:
        """Load sync state from disk or initialize fresh state if missing."""
        if not self.state_path.exists():
            return SyncState()
        try:
            raw_text = self.state_path.read_text(encoding="utf-8")
            data = json.loads(raw_text)
            return SyncState.model_validate(data)
        except Exception as e:
            logger.warning(
                "Could not parse sync state file at %s (%s). Re-initializing.", self.state_path, e
            )
            return SyncState()

    def save(self) -> None:
        """Persist current watermark state to disk as formatted JSON."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(self.state.model_dump_json(indent=2), encoding="utf-8")

    def get_watermark(
        self,
        source_id: str,
        default_lookback_days: int = DEFAULT_INITIAL_LOOKBACK_DAYS,
    ) -> datetime:
        """Get the watermark timestamp for a specific source stream.

        If the source has never been synced, defaults to (now - default_lookback_days).
        """
        if source_id in self.state.sources:
            return self.state.sources[source_id]
        return datetime.now(UTC) - timedelta(days=default_lookback_days)

    def update_source_watermark(self, source_id: str, timestamp: datetime | None = None) -> None:
        """Update the watermark for a given source to a timestamp (defaulting to UTC now)."""
        ts = timestamp or datetime.now(UTC)
        self.state.sources[source_id] = ts

    def record_sync_completion(
        self,
        ingested_count: int,
        qualified_count: int,
        evaluated_count: int,
        completed_at: datetime | None = None,
    ) -> None:
        """Record a successful full sync run and append to execution history."""
        now = completed_at or datetime.now(UTC)
        self.state.last_sync_at = now
        record = SyncRunRecord(
            synced_at=now,
            ingested_count=ingested_count,
            qualified_count=qualified_count,
            evaluated_count=evaluated_count,
        )
        self.state.history.append(record)
        if len(self.state.history) > 50:
            self.state.history = self.state.history[-50:]
        self.save()

    def reset_all(self, lookback_days: int = DEFAULT_INITIAL_LOOKBACK_DAYS) -> None:
        """Reset all source watermarks back to (now - lookback_days)."""
        reset_time = datetime.now(UTC) - timedelta(days=lookback_days)
        self.state.last_sync_at = None
        for k in self.state.sources:
            self.state.sources[k] = reset_time
        self.save()

    def reset_source(
        self,
        source_id: str,
        lookback_days: int = DEFAULT_INITIAL_LOOKBACK_DAYS,
    ) -> None:
        """Reset a single source watermark back to (now - lookback_days)."""
        reset_time = datetime.now(UTC) - timedelta(days=lookback_days)
        self.state.sources[source_id] = reset_time
        self.save()
