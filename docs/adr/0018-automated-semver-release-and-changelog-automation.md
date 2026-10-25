# ADR 0018: Automated SemVer Release Tagging and Changelog Automation via Release Please

## Status
Accepted

## Context
As the Trend Horizon Radar project matures, continuous delivery requires a deterministic, automated release mechanism that eliminates manual version increments, manual tag creation, and handcrafted release notes.

The repository strictly enforces **Conventional Commits** (`feat:`, `fix:`, `refactor:`, `perf:`, `docs:`, `BREAKING CHANGE:`). These commit conventions encode semantic intent directly into the git history. We need an automated release pipeline that:
1. Calculates the next Semantic Version (SemVer: `MAJOR.MINOR.PATCH`) based on unreleased commits.
2. Maintains an up-to-date, categorized `CHANGELOG.md` file.
3. Synchronizes version numbers across `pyproject.toml` and git tags.
4. Builds and attaches production distribution packages (Python wheels, source archives, and static web dashboard bundles) to GitHub Releases.
5. Provides human-in-the-loop governance so releases are reviewed before being published, without requiring manual authoring.

## Options Considered

### Option 1: Release PR Pattern with Google's `release-please` (Selected)
- A GitHub Actions workflow runs on every push to `main` using `googleapis/release-please-action`.
- Release Please analyzes commit messages since the last release tag and opens/updates a single **Release PR** (e.g., `chore: release 0.2.0`).
- The PR contains:
  - The updated version in `pyproject.toml`.
  - The newly generated sections in `CHANGELOG.md` categorized by type (Features, Bug Fixes, Documentation, Breaking Changes).
- When the engineer merges the Release PR into `main`, Release Please tags the commit (e.g. `v0.2.0`), creates a GitHub Release, and triggers downstream packaging steps to upload distribution artifacts.
- *Pros:*
  - Full governance: releases happen only when the Release PR is merged.
  - Zero manual changelog editing or version tagging.
  - Completely auditable via standard pull request review workflows.
- *Trade-offs:*
  - Requires `pull-requests: write` and `contents: write` permissions for the workflow token.

### Option 2: Autonomous Direct-to-Tag (`python-semantic-release`)
- Evaluates commits on push to `main` and immediately tags and publishes releases without opening a PR.
- *Pros:* Fully hands-off.
- *Trade-offs:* Can create excessive releases for individual feature pushes; lacks a staging period where release notes can be reviewed.

### Option 3: Manual Git Tagging
- Relies on engineers manually running `git tag vX.Y.Z` and pushing tags.
- *Pros:* No new tooling.
- *Trade-offs:* High risk of human error, version drift, and inconsistent changelog formatting.

## Decision Rationale
We adopt **Option 1: Release PR Pattern with `release-please`**:
1. It maintains strict alignment with our pair programming and release protocols: every release is captured as a PR with clear diffs before tags are applied.
2. Native support for Python projects (`pyproject.toml`) and standard Markdown changelogs.
3. Automated artifact packaging: when the Release PR is merged, GitHub Actions builds the Python wheel/sdist via `uv build`, packages the static web dashboard (`radar-web-dashboard.tar.gz`), and uploads them to the GitHub Release.

## Consequences

### Positive
- Fully automated SemVer tracking with zero manual version bookkeeping.
- Transparent, beautiful `CHANGELOG.md` maintained in the root directory.
- Releases are packaged with verifiable build artifacts attached directly on GitHub.
- Full parity between remote GitHub Actions and project standards.

### Negative / Trade-offs
- Requires initial setup of `.release-please-config.json` and `.release-please-manifest.json`.
- Developers must continue writing disciplined Conventional Commit messages.
