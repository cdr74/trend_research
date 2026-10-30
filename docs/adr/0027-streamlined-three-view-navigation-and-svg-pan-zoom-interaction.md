# ADR 0027: Streamlined Three-View Navigation and SVG Pan-Zoom Interaction

## Status
Accepted (Auto-Approved by Operator)

## Context
As the evaluated intelligence dataset expanded to over 300 items across 15 active source streams, two distinct UX limitations emerged in the web dashboard (`web/`):
1. **Redundancy of the Scatter Matrix:**
   - The *Scatter Matrix* view plotted Viability ($0.0 \to 1.0$) against Hype ($0.0 \to 1.0$).
   - However, the 4 ThoughtWorks-style radar rings (`Adopt`, `Trial`, `Assess`, `Hold`) are already mathematically derived from Viability and Hype.
   - Consequently, the Scatter Matrix largely duplicated the distribution of the Radar Quadrant while stripping away the 6 Quality Engineering pillar slices and dynamic topic clusters. At 300+ items, it degenerated into dense, unreadable clusters.
2. **Visual Clutter & Scale Invariance in Dense Quadrants:**
   - In both the **Radar Quadrant** (`RadarChart.tsx`) and **Semantic Cluster Map** (`ClusterMap.tsx`), hundreds of blips are plotted inside static SVG viewports ($800 \times 800$ and $760 \times 560$).
   - In dense rings (such as `Assess` and `Trial`) or tightly clustered technique groups (e.g. mutation testing frameworks), blips and text labels overlap without a mechanism to drill in and inspect individual tools spatially.

---

## Decision Matrix & Evaluation

### 1. View Navigation Streamlining (Option A)
* **Decision:**
  - Deprecate and remove the Scatter Matrix view (`ScatterPlot.tsx`).
  - Streamline the primary view navigation to three clear, non-redundant perspectives:
    1. **Radar Quadrant:** Spatial ring-and-pillar lifecycle topology (`Adopt`, `Trial`, `Assess`, `Hold` across 6 QE pillars).
    2. **Matrix Table:** Full-fidelity tabular data grid with multi-column sorting, secondary filter dropdowns, and search.
    3. **Semantic Clusters:** 2D UMAP projection visualizing semantic and architectural similarity from 1536-dimensional embeddings.
  - *Rationale:* Eliminates cognitive redundancy, clarifies navigation, and directs user focus to the most informative analytical projections.

### 2. Zero-Dependency SVG Pan & Zoom Interaction Architecture
* **Decision:**
  - Implement a reusable React hook `useZoomPan` managing 2D affine transform matrix state `(x, y, k)` where:
    - $k$ represents zoom scale bounded within $[0.6, 6.0]$.
    - $(x, y)$ represents translation coordinates in canvas pixels.
  - **Interaction Ergonomics:**
    - **Mouse Wheel / Trackpad Pinch:** Zooms towards the cursor coordinate so the point under the cursor remains invariant during scaling.
    - **Click & Drag (Pan):** Smooth translation across the canvas with drag detection threshold ($> 3\text{px}$) to avoid hijacking single-click blip selection events.
    - **Floating HUD Controls:** Subtle overlay pill providing on-screen `[+]`, `[-]`, and `[Reset View]` buttons alongside current zoom percentage.
  - **Scale Invariance for Blip Ergonomics:**
    - Blip radiuses scale inversely ($r \propto 1/\sqrt{k}$) so points never swell into giant circles when zooming into dense clusters.
    - Labels remain crisp and readable without overlapping adjacent points.
  - **Zero Bundle Overhead:**
    - Avoid heavy external dependencies (e.g. `d3-zoom`); implement purely through native React SVG event handlers and CSS transforms.

---

## Consequences

### Positive
- Intuitive, frictionless exploration of dense 300+ item clusters across both Radar and Semantic Cluster views.
- Top-level view navigation is clean, purposeful, and free of redundant viability/hype scatter plots.
- Zero added external npm package dependencies; static build bundle size remains compact (< 190 kB gzipped).

### Negative / Trade-offs
- Operators who previously used the 2D viability/hype scatter plot can rely on the Matrix Table (sorting by Viability or Hype score) or the Radar Quadrant.
