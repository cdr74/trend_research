# ADR 0005: Visualization Strategy and Radar User Interface

## Status
Accepted

## Context
The Radar produces structured intelligence on AI-driven software test engineering tools, papers, and practices. Users (software engineering leaders, enterprise architects, quality directors) require rich filtering and varied visualization perspectives:
1. **Radar Quadrant View:** Standard 4-ring radar (Adopt, Trial, Assess, Hold) segmented across the 6 QE categories.
2. **Multi-dimensional Filtering:** Interactive filtering by QE pillar, enterprise viability score, anti-hype score, evidence tier (Academic, Open Source, Post-Mortem, Vendor), banking risk tags (VPC egress, non-determinism, data leaks), and time window.
3. **Data Grid / Deep Dossier View:** Searchable tabular view for side-by-side comparison of tools and review of adversarial skeptic findings.
4. **Semantic Cluster View:** Visualizing semantic embedding projections (from `pgvector`) to identify tool clusters and detect overlapping "wrapper" tools.
5. **Static Executive Briefing:** Markdown and standalone HTML digests for distribution in enterprise newsletters or leadership updates.

We need an architecture that maximizes visualization flexibility, minimizes operational maintenance, and supports both local development and static publication.

## Options Considered
1. **Decoupled Architecture: Versioned JSON/API + Modern Static SPA (Selected - Most Flexible)**:
   - Backend exports a comprehensive, versioned `radar.json` dataset and optionally serves a FastAPI REST query interface.
   - Frontend is built as a lightweight, modular Single Page Application (Vite + React / TypeScript + Tailwind CSS with D3 / TanStack Table).
   - **Why this is the most flexible option:**
     - Runs locally or builds to pure static assets (HTML/CSS/JS) deployable to GitHub Pages, enterprise object storage, or internal documentation portals with zero server management.
     - Supports modular visualizers: Radar Quad-Quadrant, Scatter Plot (Viability vs Hype), Filterable Matrix Table, and Semantic Cluster Map.
     - Client-side instant filtering across thousands of signals without server round-trips.
     - Can consume either static `radar.json` snapshots or a live local PostgreSQL/FastAPI API.
2. **Python Notebooks / Streamlit**:
   - Rapid prototyping, but difficult to brand, poor mobile/presentation ergonomics, slow UI reactivity with complex multi-view visualizations, and requires a persistent Python server.
3. **Pre-canned ThoughtWorks Radar Static Generator**:
   - Easy to start, but rigid and inflexible: does not support custom multidimensional filters, scatter plots, semantic clustering, or rich banking risk dossiers.
4. **Markdown / CLI Only**:
   - Zero UI overhead, but lacks the interactive exploratory visual power required by enterprise decision makers.

## Decision Rationale
We adopt a **Decoupled Architecture**:
- **Backend / Core Engine:** Generates versioned `radar.json` artifacts, provides a CLI query tool, and generates automated bi-weekly Markdown digests (`reports/YYYY-WW.md`).
- **Web Dashboard (`web/`):** A modern, decoupled Vite + React + TypeScript application with Tailwind CSS and D3 visualization primitives.
  - Features dynamic view switching (Radar View, Matrix Table View, Scatter Matrix View, Semantic Map View).
  - Rich filter sidebar (Ring, Category, Evidence Tier, Score Thresholds, Risk Flags).
  - Self-contained build (`dist/`) suitable for automated deployment to GitHub Pages via CI/CD.

## Consequences
### Positive
- Maximum UI/UX flexibility: unlimited visual layouts and instant client-side filtering.
- Zero server hosting costs or infrastructure overhead when published as static GitHub Pages.
- Clean separation of concerns between Python intelligence pipeline and TypeScript visualization layer.

### Negative / Trade-offs
- Introduces Node.js / TypeScript build step in CI for web dashboard packaging alongside the Python pipeline.
