import React, { useEffect, useState, useMemo } from "react";
import { RadarData, RadarItem, RadarRing, QECategory, EvidenceTier } from "./types";
import { RadarChart } from "./components/RadarChart";
import { TableView } from "./components/TableView";
import { ScatterPlot } from "./components/ScatterPlot";
import { ClusterMap } from "./components/ClusterMap";
import { FilterSidebar } from "./components/FilterSidebar";
import { ItemDetailModal } from "./components/ItemDetailModal";
import { parseSearchQuery, matchesQuery } from "./utils/tokenSearch";

type ViewMode = "radar" | "table" | "scatter" | "cluster";

export const App: React.FC = () => {
  const [data, setData] = useState<RadarData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState<ViewMode>("radar");

  // Filter States
  const [selectedRings, setSelectedRings] = useState<Set<RadarRing>>(
    new Set(["Adopt", "Trial", "Assess", "Hold"])
  );
  const [selectedCategories, setSelectedCategories] = useState<Set<QECategory>>(
    new Set([
      "Spec & Model",
      "Test Synthesis",
      "Execution & Optimization",
      "Triage & Self-Healing",
      "Agent Systems",
      "Governance & Evals",
    ])
  );
  const [selectedEvidenceTiers, setSelectedEvidenceTiers] = useState<Set<EvidenceTier>>(
    new Set([
      "Academic Peer-Reviewed",
      "Open Source Repo",
      "Engineering Post-Mortem",
      "Vendor Announcement",
    ])
  );
  const [selectedTrack, setSelectedTrack] = useState<"all" | "testing" | "evaluation">("all");
  const [minViability, setMinViability] = useState<number>(0.0);
  const [maxHype, setMaxHype] = useState<number>(1.0);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [selectedItem, setSelectedItem] = useState<RadarItem | null>(null);

  useEffect(() => {
    fetch("./radar.json")
      .then((res) => res.json())
      .then((json: RadarData) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load radar.json:", err);
        setLoading(false);
      });
  }, []);

  const toggleRing = (ring: RadarRing) => {
    setSelectedRings((prev) => {
      const next = new Set(prev);
      if (next.has(ring)) next.delete(ring);
      else next.add(ring);
      return next;
    });
  };

  const toggleCategory = (cat: QECategory) => {
    setSelectedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
  };

  const toggleEvidenceTier = (tier: EvidenceTier) => {
    setSelectedEvidenceTiers((prev) => {
      const next = new Set(prev);
      if (next.has(tier)) next.delete(tier);
      else next.add(tier);
      return next;
    });
  };

  const resetFilters = () => {
    setSelectedRings(new Set(["Adopt", "Trial", "Assess", "Hold"]));
    setSelectedCategories(
      new Set([
        "Spec & Model",
        "Test Synthesis",
        "Execution & Optimization",
        "Triage & Self-Healing",
        "Agent Systems",
        "Governance & Evals",
      ])
    );
    setSelectedEvidenceTiers(
      new Set([
        "Academic Peer-Reviewed",
        "Open Source Repo",
        "Engineering Post-Mortem",
        "Vendor Announcement",
      ])
    );
    setMinViability(0.0);
    setMaxHype(1.0);
    setSearchTerm("");
    setSelectedTrack("all");
  };

  const testingCount = useMemo(
    () => (data ? data.items.filter((it) => (it.track || "testing") === "testing").length : 0),
    [data]
  );
  const evaluationCount = useMemo(
    () => (data ? data.items.filter((it) => it.track === "evaluation").length : 0),
    [data]
  );

  const filteredItems = useMemo(() => {
    if (!data) return [];
    const parsedQuery = parseSearchQuery(searchTerm);

    return data.items.filter((item) => {
      if (selectedTrack !== "all") {
        const itemTrack = item.track || "testing";
        if (itemTrack !== selectedTrack) return false;
      }
      if (!selectedRings.has(item.recommended_ring)) return false;
      if (!selectedCategories.has(item.category)) return false;
      if (!selectedEvidenceTiers.has(item.evidence_tier)) return false;
      if (item.viability_score < minViability) return false;
      if (item.hype_score > maxHype) return false;
      if (!matchesQuery(item, parsedQuery)) return false;
      return true;
    });
  }, [
    data,
    selectedTrack,
    selectedRings,
    selectedCategories,
    selectedEvidenceTiers,
    minViability,
    maxHype,
    searchTerm,
  ]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center text-slate-400">
        Loading Horizon Radar Intelligence...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0b0f19] flex flex-col font-sans">
      {/* Top Header */}
      <header className="border-b border-[#1f293d] bg-[#121826]/80 backdrop-blur sticky top-0 z-40 px-8 py-4 flex justify-between items-center">
        <div>
          <div className="flex items-center space-x-3">
            <span className="w-3 h-3 rounded-full bg-emerald-400 animate-pulse"></span>
            <h1 className="text-xl font-bold tracking-tight text-slate-100">
              AI Test Engineering Horizon Radar
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Deterministic Anti-Hype Penalties & Tier-1 Banking Enterprise Viability Vetting
          </p>
        </div>

        {/* 4 View Modes Switcher */}
        <div className="flex items-center space-x-1.5 bg-[#0b0f19] p-1 rounded-xl border border-[#1f293d]">
          <button
            onClick={() => setActiveView("radar")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeView === "radar"
                ? "bg-blue-600 text-white shadow"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Radar Quadrant
          </button>
          <button
            onClick={() => setActiveView("table")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeView === "table"
                ? "bg-blue-600 text-white shadow"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Matrix Table ({filteredItems.length})
          </button>
          <button
            onClick={() => setActiveView("scatter")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeView === "scatter"
                ? "bg-blue-600 text-white shadow"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Scatter Matrix
          </button>
          <button
            onClick={() => setActiveView("cluster")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeView === "cluster"
                ? "bg-blue-600 text-white shadow"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Semantic Clusters (UMAP)
          </button>
        </div>
      </header>

      {/* Sub-Header / Dual-Track Switcher Bar */}
      <div className="border-b border-[#1f293d] bg-[#101622] px-8 py-2.5 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-xs uppercase font-bold text-slate-400 tracking-wider mr-2">
            Domain Track:
          </span>
          <button
            onClick={() => setSelectedTrack("all")}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              selectedTrack === "all"
                ? "bg-slate-700 text-white shadow"
                : "text-slate-400 hover:text-slate-200 hover:bg-[#1a233a]"
            }`}
          >
            All Tracks ({data?.items.length ?? 0})
          </button>
          <button
            onClick={() => setSelectedTrack("testing")}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              selectedTrack === "testing"
                ? "bg-blue-600 text-white shadow"
                : "text-slate-400 hover:text-slate-200 hover:bg-[#1a233a]"
            }`}
          >
            Software Testing ({testingCount})
          </button>
          <button
            onClick={() => setSelectedTrack("evaluation")}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
              selectedTrack === "evaluation"
                ? "bg-purple-600 text-white shadow"
                : "text-slate-400 hover:text-slate-200 hover:bg-[#1a233a]"
            }`}
          >
            AI Evaluation ({evaluationCount})
          </button>
        </div>

        <div className="text-xs text-slate-400">
          Showing <span className="font-semibold text-slate-200">{filteredItems.length}</span> of{" "}
          <span className="font-semibold text-slate-200">{data?.items.length ?? 0}</span> evaluated signals
        </div>
      </div>

      {/* Main Container */}
      <main className="flex-1 px-8 py-6 flex space-x-8">
        {/* Left Filter Sidebar */}
        <FilterSidebar
          selectedRings={selectedRings}
          onToggleRing={toggleRing}
          selectedCategories={selectedCategories}
          onToggleCategory={toggleCategory}
          selectedEvidenceTiers={selectedEvidenceTiers}
          onToggleEvidenceTier={toggleEvidenceTier}
          minViability={minViability}
          onChangeMinViability={setMinViability}
          maxHype={maxHype}
          onChangeMaxHype={setMaxHype}
          searchTerm={searchTerm}
          onChangeSearchTerm={setSearchTerm}
          onResetFilters={resetFilters}
        />

        {/* Center Presentation View */}
        <div className="flex-1 flex flex-col items-center">
          {activeView === "radar" && (
            <RadarChart
              items={filteredItems}
              selectedItem={selectedItem}
              onSelectItem={setSelectedItem}
            />
          )}
          {activeView === "table" && (
            <TableView
              items={filteredItems}
              selectedItem={selectedItem}
              onSelectItem={setSelectedItem}
            />
          )}
          {activeView === "scatter" && (
            <ScatterPlot
              items={filteredItems}
              selectedItem={selectedItem}
              onSelectItem={setSelectedItem}
            />
          )}
          {activeView === "cluster" && (
            <ClusterMap
              items={filteredItems}
              selectedItem={selectedItem}
              onSelectItem={setSelectedItem}
            />
          )}
        </div>
      </main>

      {/* Modal Inspector */}
      <ItemDetailModal item={selectedItem} onClose={() => setSelectedItem(null)} />
    </div>
  );
};
