"""Container lifecycle management for local PostgreSQL + pgvector database."""

import asyncio
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from radar.db.session import check_db_health, init_db


def detect_compose_command() -> list[str] | None:
    """Detect available container compose tool (podman or docker)."""
    if shutil.which("podman"):
        return ["podman", "compose", "up", "-d"]
    if shutil.which("docker"):
        return ["docker", "compose", "up", "-d"]
    return None


def find_compose_file(start_path: Path | None = None) -> Path | None:
    """Locate compose.yaml or docker-compose.yml in start_path or package root."""
    search_paths = [
        start_path or Path.cwd(),
        Path(__file__).resolve().parents[3],
    ]
    for p in search_paths:
        for fname in ("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml"):
            candidate = p / fname
            if candidate.exists():
                return candidate
    return None


async def start_db_container(
    project_root: Path | None = None,
    timeout_seconds: float = 15.0,
) -> bool:
    """Launch the database container using podman/docker compose and await readiness."""
    cmd = detect_compose_command()
    if not cmd:
        return False

    compose_file = find_compose_file(project_root)
    if not compose_file:
        return False

    work_dir = compose_file.parent

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(work_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, _ = await proc.communicate()
        if proc.returncode != 0:
            return False

        # Poll database health until responsive or timeout
        poll_interval = 0.5
        max_attempts = int(timeout_seconds / poll_interval)
        for _ in range(max_attempts):
            await asyncio.sleep(poll_interval)
            if await check_db_health():
                await init_db()
                return True
    except Exception:
        return False

    return False


async def ensure_db_running(
    auto_start: bool = False,
    prompt_fn: Callable[[], bool] | None = None,
    interactive: bool | None = None,
    project_root: Path | None = None,
) -> bool:
    """Verify that the database is healthy, offering to start it with user consent if offline.

    Args:
        auto_start: If True, bypass prompting and attempt to start the container immediately.
        prompt_fn: Custom callable returning bool for user confirmation.
        interactive: Override interactive terminal check (defaults to sys.stdin.isatty()).
        project_root: Optional directory containing compose.yaml.

    Returns:
        True if the database is running and ready, False otherwise.
    """
    if await check_db_health():
        return True

    # If auto-start flag is set, proceed without asking
    if auto_start:
        return await start_db_container(project_root=project_root)

    # Determine interactivity
    is_tty = sys.stdin.isatty() if interactive is None else interactive
    if not is_tty or prompt_fn is None:
        return False

    # Ask user for consent
    user_agreed = prompt_fn()
    if user_agreed:
        return await start_db_container(project_root=project_root)

    return False
