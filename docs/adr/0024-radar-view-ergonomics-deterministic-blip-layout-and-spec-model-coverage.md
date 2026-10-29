# ADR 0024: Radar View Ergonomics, Deterministic Blip Layout, and Spec & Model Coverage

## Status
Accepted (Phase 2 Autonomous Implementation)

## Context
Following Milestone 8's dynamic bounded topic convergence, user experience feedback across both visual and domain dimensions highlighted five ergonomic and domain gaps:

1. **Matrix Table Interaction:** The tabular view lacks per-column sorting (ascending/descending/reset) and per-column filtering, making exploratory queries cumbersome when scanning specific metrics (e.g. highest viability, specific themes, or corroboration counts).
2. **Radar Overview Label Clipping:** The radar SVG viewport (`viewBox="0 0 800 800"`) tightly bounds the outer radius ($r = 370$ px), placing category pillar labels at the extreme outer coordinates ($y \approx 0$ and $y \approx 800$). In standard browser viewports, the top and bottom labels ("Spec & Model", "Governance & Evals") are clipped by container boundaries.
3. **Radar Blip Spatial Instability ("Hopping"):** In [`RadarChart.tsx`](file:///home/chris/dev/trend_research/web/src/components/RadarChart.tsx), blip coordinates within a ring band are computed using `index`—the transient array index of the item within the currently filtered array (`index * 37`, `index * 17`). Consequently, applying any filter alters the index of remaining items, causing blips to jump erratically across the radar.
4. **Scatter Matrix Text Collisions:** In [`ScatterPlot.tsx`](file:///home/chris/dev/trend_research/web/src/components/ScatterPlot.tsx), full text labels (`item.name`) are rendered statically next to every data point. Because high-viability items cluster at similar coordinates (e.g. 8 mutation testing tools at hype $\approx 0.15$ and viability $\approx 0.88$), their text overlays produce an unreadable typographic collision.
5. **Empty "Spec & Model" Pillar:** In the current live database of 23 signals, the "Spec & Model" SDLC pillar has 0 blips because initial ingestion runs omitted property-based testing and specification contract tools (e.g., `Hypothesis`, `Schemathesis`, `fast-check`).

---

## Decision Matrix & Evaluation

### 1. Matrix Table: Per-Column Sort & Filter
* **Option A: External Heavy Table Library (TanStack Table / AG-Grid):**
  - *Pros:* Rich feature set out of the box.
  - *Cons:* Adds 100KB+ to frontend bundle; introduces third-party abstraction drift and CSS overrides.
* **Option B: Lightweight Native React State Machine (Selected):**
  - Implement a clean sorting state machine (`sortField`, `sortDirection`: `'asc' | 'desc' | null`) with custom comparators for rings (`Adopt` > `Trial` > `Assess` > `Hold`), trajectories, and numbers.
  - Add an integrated filter bar row beneath the table headers supporting typed input search and categorical dropdowns (`Track`, `Theme`, `Pillar`, `Ring`, `Trajectory`, `Evidence Tier`).
  - *Rationale:* Zero external dependencies, pure TypeScript compliance, sub-millisecond execution on client side.

### 2. Radar Overview Viewport & Label Breathing Room
* **Decision:**
  - Increase the SVG viewBox canvas with 60px of perimeter padding (`viewBox="-60 -60 920 920"`).
  - Recalibrate label radial positioning to $r = 415$ px with contextual SVG alignment:
    - Top quadrants: `dominant-baseline="auto"`
    - Bottom quadrants: `dominant-baseline="hanging"`
    - Left/Right: `text-anchor="start" | "end" | "middle"`.
  - Remove restrictive container clipping (`overflow-hidden`) on the radar card to allow soft label halos.

### 3. Invariant Deterministic Radar Blip Layout
* **Decision:**
  - Replace transient array `index` with an invariant item identity hash:
    $$\text{hash} = \text{FNV-1a}(\text{item.id})$$
  - The radial offset within the ring band and angular offset within the category slice are derived purely from $\text{hash} \pmod N$:
    $$r = r_{\text{min}} + \Delta r \cdot 0.25 + \left(\frac{\text{hash} \pmod{1000}}{1000}\right) \cdot (\Delta r \cdot 0.50)$$
    $$\theta_{\text{offset}} = \left(\frac{\text{hash} \pmod{300}}{10} - 15\right) \cdot \frac{\pi}{180}$$
  - *Consequence:* An item's coordinates $(x, y)$ on the radar remain 100% stable regardless of which filters or search tokens are active. Filtering only toggles visibility, eliminating all hopping.

### 4. Scatter Matrix Label Collision Resolution
* **Decision:**
  - Switch to point-first rendering with glowing blips and clear ring color coding.
  - Static permanent text labels are suppressed by default. Full labels and interactive inspection cards are displayed dynamically on hover or selection.
  - Add a "Show All Labels" toggle button in the Scatter Matrix header for users who explicitly want static text overlays.

### 5. Spec & Model Pillar Ingestion & Dynamic Convergence
* **Decision:**
  - Ingest and evaluate canonical open-source property-based and specification-driven testing frameworks:
    1. `HypothesisWorks/hypothesis` (Python property-based generative testing).
    2. `schemathesis/schemathesis` (OpenAPI/GraphQL specification contract testing).
    3. `dubzzz/fast-check` (TypeScript/JavaScript property testing).
  - Execute Stage 1–4 pipeline to synthesize a 7th dynamic theme: **`Model-Based & Property-Driven Testing`**.
  - All 3 items inherit consensus pillar `QECategory.SPEC_AND_MODEL`, populating the empty slice on the radar. Total active themes remain at 7, well below the 12-theme ceiling.

---

## Consequences

### Positive
- Table view provides immediate spreadsheet-grade sorting and per-column filtering.
- Radar labels are fully legible without viewport truncation across standard screen resolutions.
- Filtering radar items is visually calm and deterministic; blips never hop.
- Scatter matrix is clean, readable, and free of typographic collisions.
- All 6 SDLC Quality Engineering pillars are represented with verified, authentic tooling.

### Negative / Trade-offs
- Adding 3 property-based tools increases the radar item count from 23 to 26 items (well within database capacity and UI performance limits).
