# ADR 0020: Interactive Database Lifecycle Probing and User Consent Startup

## Status
Accepted

## Context
The Trend Horizon Radar relies on a local PostgreSQL 16 instance with the `pgvector` extension, declared in `compose.yaml` and orchestrated via Podman (or Docker). When running locally in Windows Subsystem for Linux (WSL2) or Linux developer workstations:
1. The container maintains persistent state across sessions in the `pgdata` volume and is configured with `restart: unless-stopped`.
2. However, when the host machine reboots or WSL shuts down (`wsl --shutdown`), all background container runtimes terminate.
3. Upon reopening WSL, running `uv run radar sync` previously detected that port 5432 was unresponsive and silently skipped database persistence, operating in ephemeral/offline mode.
4. Requiring the developer to remember and execute `podman compose up -d` in a separate command breaks the frictionless CLI experience. Conversely, unconditionally starting container background processes without operator consent violates user control and may fail in CI/CD or resource-constrained environments.

The user requirement specifies:
> "Agree, but add a user consent: if db is not running ask user for input to start it."

## Decision
We implement an **interactive database lifecycle probe with explicit user consent**:

1. **Lifecycle Engine (`src/radar/db/container.py`):**
   - Detects available container orchestrators (`podman compose`, `podman-compose`, `docker compose`).
   - Checks database health via `check_db_health()`.
   - If unresponsive, provides `start_db_container()` to invoke the compose up command asynchronously and poll health checks until PostgreSQL is ready (timeout: 15s).
   - Once healthy, invokes `init_db()` to guarantee table schemas and `pgvector` extensions exist.

2. **Interactive Consent Gate in CLI (`src/radar/presentation/cli.py`):**
   - Before executing operations that persist or query data (`radar sync`, `radar evaluate`, `radar query`, `radar inspect`), the CLI checks `check_db_health()`.
   - If the database is healthy: proceeds immediately with zero overhead.
   - If the database is offline and standard input is interactive (TTY):
     - Displays:
       `[bold yellow]PostgreSQL database (radar-postgres) is not running on localhost:5432.[/bold yellow]`
     - Prompts user with Rich:
       `Would you like to start it now via 'podman compose up -d'? [Y/n]: `
     - If approved (`y` / `yes`): starts the container, waits for readiness, initializes schemas, and resumes execution seamlessly.
     - If declined (`n` / `no`): informs the operator that the run will proceed in offline/in-memory mode without persistence (or aborts for DB-exclusive operations like `--sql`).
   - If the environment is non-interactive (CI runner, piped stdin) or `--mock` is active: does not prompt; defaults to offline fallback.

3. **Command Line Flag Overrides:**
   - `--auto-start-db`: Bypass the prompt and start the container automatically if offline.
   - `--no-db`: Explicitly run in offline mode without probing or prompting.

## Consequences

### Positive
- **Frictionless WSL Experience:** The engineer never has to manually open another terminal to type `podman compose up -d` after a machine reboot.
- **User Control & Transparency:** Containers are never silently spawned without explicit operator approval.
- **Safe CI/CD & Scripting Parity:** Headless and automated environments are guarded against hanging on interactive prompts.

### Negative / Trade-Offs
- Adds a small startup probe latency (~5ms when DB is up; ~1s when starting from cold stop).
- Requires subprocess execution permissions in the local environment for `podman` or `docker`.
