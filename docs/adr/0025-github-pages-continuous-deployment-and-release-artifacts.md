# ADR 0025: GitHub Pages Continuous Deployment and Release Distribution Artifacts

## Status
Accepted (Phase 2 Autonomous Implementation)

## Context
The AI Test Engineering Trend Horizon Radar features a decoupled interactive web dashboard built with Vite, React, TypeScript, Tailwind CSS, and D3/SVG (`web/`). The application is designed to be fully static, consuming an exported data bundle (`web/public/radar.json`) containing all evaluated radar items, dynamic themes, categorizations, and multi-lens adversarial dossiers.

Stakeholders and testing leaders need:
1. **Zero-Install Public Accessibility:** A hosted, continuously updated interactive radar accessible directly in the browser via GitHub Pages (`https://cdr74.github.io/trend_research/`) without requiring local Python environments, Node.js runtimes, or database containers.
2. **Deterministic Release Bundles:** Self-contained, downloadable web dashboard packages (`.tar.gz` and `.zip`) attached directly to each GitHub Release so teams can host the radar internally behind air-gapped corporate intranets or open it offline.
3. **Continuous Deployment Integrity:** Automated deployment on every push to `main` and on every published release via GitHub Actions, while ensuring the workflow preserves the real evaluated intelligence dataset rather than clobbering it with mock fallback fixtures.

---

## Decision Matrix & Evaluation

### 1. GitHub Pages Trigger Topology
* **Option A: Manual Execution Only (`workflow_dispatch`):**
  - *Cons:* Prone to neglect; live site drifts from repository state.
* **Option B: Continuous Push & Release Deployment (Selected):**
  - Configure `.github/workflows/pages.yml` with triggers:
    - `push` to `main`: Deploys updates whenever evaluated radar data, frontend code, or documentation lands on `main`.
    - `release` (`published`): Ensures every formal version release triggers a fresh deployment.
    - `workflow_dispatch`: Retains manual operator trigger for on-demand redeployment.
  - *Rationale:* Ensures the public site mirrors the latest accepted state with zero human intervention.

### 2. Radar Data Bundle Preservation vs. Fallback Generation
* **Context:** In CI environments without an active PostgreSQL container, previous workflow steps ran `uv run radar export ... --mock`, which would overwrite the committed 26-item production dataset with a 6-item mock fixture.
* **Decision:**
  - Check for the existence of `web/public/radar.json` at the start of the deployment workflow.
  - When `web/public/radar.json` is present in the repository, use it directly and skip downloading Python and heavy ML dependencies (`umap-learn`, `scipy`), reducing deploy times from ~3 minutes to under 30 seconds.
  - If `web/public/radar.json` is missing (e.g. in experimental branches), execute a graceful fallback using `uv sync --all-extras` and `radar export --mock` so the build never fails.

### 3. Release Distribution Asset Packaging
* **Context:** Release Please automatically generates releases when Release PRs merge. Previously, `.github/workflows/release.yml` packaged only a `.tar.gz` archive of the web build.
* **Decision:**
  - Build static web dashboard bundle (`web/dist/`) during the release job.
  - Package both `radar-web-dashboard.tar.gz` (for Linux/macOS) and `radar-web-dashboard.zip` (for Windows / universal extraction) into root `dist/`.
  - Use Python standard library's `shutil.make_archive` to ensure cross-platform zip generation without relying on external system utilities.
  - Upload both web archives alongside backend Python wheels and source distributions using `gh release upload <tag> dist/* --clobber`.

### 4. Subpath Routing & Relative Asset Base
* **Decision:**
  - Maintain `base: "./"` in `web/vite.config.ts`.
  - Relative asset paths allow the compiled SPA to function identically whether served at the root domain, under the GitHub Pages subpath (`/trend_research/`), or opened directly from local disk via static file servers (`python3 -m http.server`).

---

## Consequences

### Positive
- **Instant Stakeholder Access:** QE leaders, enterprise architects, and executives can immediately interact with the radar at `https://cdr74.github.io/trend_research/`.
- **Air-Gapped Compliance:** Regulated enterprise teams can download `radar-web-dashboard.zip` from GitHub Releases and host it internally on private object stores (AWS S3, MinIO) or air-gapped web servers with zero external network dependencies.
- **Fast CI Execution:** Deployment workflow completes in < 30 seconds by avoiding redundant ML environment synchronization when static data is already validated and committed.
- **Auditability:** Every release asset in GitHub Releases contains an exact snapshot of the radar intelligence at that SemVer tag.

### Negative / Trade-offs
- The repository administrator must ensure GitHub Pages is enabled in repository settings with Source set to "GitHub Actions".
