"""Unit tests for container lifecycle management and database probing."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from radar.db.container import (
    detect_compose_command,
    ensure_db_running,
    find_compose_file,
    start_db_container,
)


def test_detect_compose_command() -> None:
    with patch("shutil.which") as mock_which:
        mock_which.side_effect = lambda cmd: "/usr/bin/podman" if cmd == "podman" else None
        assert detect_compose_command() == ["podman", "compose", "up", "-d"]

    with patch("shutil.which") as mock_which:
        mock_which.side_effect = lambda cmd: "/usr/bin/docker" if cmd == "docker" else None
        assert detect_compose_command() == ["docker", "compose", "up", "-d"]

    with patch("shutil.which", return_value=None):
        assert detect_compose_command() is None


def test_find_compose_file(tmp_path: Path) -> None:
    assert find_compose_file(tmp_path) is not None  # Falls back to package root

    custom_dir = tmp_path / "custom"
    custom_dir.mkdir()
    compose = custom_dir / "compose.yaml"
    compose.write_text("services: {}\n")

    found = find_compose_file(custom_dir)
    assert found == compose


@pytest.mark.asyncio
async def test_ensure_db_running_already_healthy() -> None:
    with (
        patch("radar.db.container.check_db_health", new_callable=AsyncMock) as mock_health,
        patch("radar.db.container.init_db", new_callable=AsyncMock) as mock_init,
    ):
        mock_health.return_value = True
        prompt = MagicMock(return_value=True)

        ready = await ensure_db_running(prompt_fn=prompt)
        assert ready is True
        prompt.assert_not_called()
        mock_init.assert_called_once()


@pytest.mark.asyncio
async def test_ensure_db_running_user_declines() -> None:
    with patch("radar.db.container.check_db_health", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = False
        prompt = MagicMock(return_value=False)

        with patch("radar.db.container.start_db_container", new_callable=AsyncMock) as mock_start:
            ready = await ensure_db_running(prompt_fn=prompt, interactive=True)
            assert ready is False
            prompt.assert_called_once()
            mock_start.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_db_running_user_agrees() -> None:
    with patch("radar.db.container.check_db_health", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = False
        prompt = MagicMock(return_value=True)

        with patch("radar.db.container.start_db_container", new_callable=AsyncMock) as mock_start:
            mock_start.return_value = True
            ready = await ensure_db_running(prompt_fn=prompt, interactive=True)
            assert ready is True
            prompt.assert_called_once()
            mock_start.assert_called_once()


@pytest.mark.asyncio
async def test_ensure_db_running_auto_start() -> None:
    with patch("radar.db.container.check_db_health", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = False
        prompt = MagicMock()

        with patch("radar.db.container.start_db_container", new_callable=AsyncMock) as mock_start:
            mock_start.return_value = True
            ready = await ensure_db_running(auto_start=True, prompt_fn=prompt)
            assert ready is True
            prompt.assert_not_called()
            mock_start.assert_called_once()


@pytest.mark.asyncio
async def test_ensure_db_running_non_interactive() -> None:
    with patch("radar.db.container.check_db_health", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = False
        prompt = MagicMock(return_value=True)

        ready = await ensure_db_running(prompt_fn=prompt, interactive=False)
        assert ready is False
        prompt.assert_not_called()


@pytest.mark.asyncio
async def test_start_db_container_subprocess_failure() -> None:
    with patch(
        "radar.db.container.detect_compose_command", return_value=["podman", "compose", "up", "-d"]
    ):
        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_proc_exec:
            mock_proc = MagicMock()
            mock_proc.communicate = AsyncMock(return_value=(b"", b"error"))
            mock_proc.returncode = 1
            mock_proc_exec.return_value = mock_proc

            success = await start_db_container()
            assert success is False
