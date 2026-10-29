import React, { useState, useMemo } from "react";
import { RadarItem, RadarRing, LifecycleStage } from "../types";

interface TableViewProps {
  items: RadarItem[];
  selectedItem: RadarItem | null;
  onSelectItem: (item: RadarItem) => void;
  selectedTheme?: string | null;
  onSelectTheme?: (theme: string | null) => void;
}

type SortField =
  | "track"
  | "name"
  | "topic_name"
  | "category"
  | "recommended_ring"
  | "lifecycle_stage"
  | "corroboration_count"
  | "viability_score"
  | "hype_score"
  | "evidence_tier";

type SortOrder = "asc" | "desc" | null;

interface ColumnFilters {
  track: string;
  name: string;
  theme: string;
  category: string;
  ring: string;
  stage: string;
  tier: string;
}

const RING_WEIGHT: Record<RadarRing, number> = {
  Adopt: 4,
  Trial: 3,
  Assess: 2,
  Hold: 1,
};

const STAGE_WEIGHT: Record<LifecycleStage, number> = {
  Consolidated: 3,
  Emerging: 2,
  Fading: 1,
};

export const TableView: React.FC<TableViewProps> = ({
  items,
  selectedItem,
  onSelectItem,
  selectedTheme,
  onSelectTheme,
}) => {
  const [sortField, setSortField] = useState<SortField | null>(null);
  const [sortOrder, setSortOrder] = useState<SortOrder>(null);
  const [filters, setFilters] = useState<ColumnFilters>({
    track: "all",
    name: "",
    theme: "all",
    category: "all",
    ring: "all",
    stage: "all",
    tier: "all",
  });

  const handleSort = (field: SortField) => {
    if (sortField !== field) {
      setSortField(field);
      setSortOrder("asc");
    } else if (sortOrder === "asc") {
      setSortOrder("desc");
    } else {
      setSortField(null);
      setSortOrder(null);
    }
  };

  const handleFilterChange = (key: keyof ColumnFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({
      track: "all",
      name: "",
      theme: "all",
      category: "all",
      ring: "all",
      stage: "all",
      tier: "all",
    });
  };

  const hasActiveFilters =
    filters.track !== "all" ||
    filters.name.trim() !== "" ||
    filters.theme !== "all" ||
    filters.category !== "all" ||
    filters.ring !== "all" ||
    filters.stage !== "all" ||
    filters.tier !== "all";

  // Derive unique options for dropdowns from full items set
  const uniqueThemes = useMemo(() => {
    const set = new Set<string>();
    items.forEach((it) => {
      if (it.topic_name) set.add(it.topic_name);
    });
    return Array.from(set).sort();
  }, [items]);

  const uniqueCategories = useMemo(() => {
    const set = new Set<string>();
    items.forEach((it) => set.add(it.category));
    return Array.from(set).sort();
  }, [items]);

  const uniqueTiers = useMemo(() => {
    const set = new Set<string>();
    items.forEach((it) => set.add(it.evidence_tier));
    return Array.from(set).sort();
  }, [items]);

  // Filtered & Sorted items
  const processedItems = useMemo(() => {
    let result = items.filter((it) => {
      if (filters.track !== "all" && (it.track || "testing") !== filters.track) return false;
      if (filters.name && !it.name.toLowerCase().includes(filters.name.toLowerCase())) return false;
      if (filters.theme !== "all" && it.topic_name !== filters.theme) return false;
      if (filters.category !== "all" && it.category !== filters.category) return false;
      if (filters.ring !== "all" && it.recommended_ring !== filters.ring) return false;
      if (filters.stage !== "all" && it.lifecycle_stage !== filters.stage) return false;
      if (filters.tier !== "all" && it.evidence_tier !== filters.tier) return false;
      return true;
    });

    if (sortField && sortOrder) {
      result = [...result].sort((a, b) => {
        let valA: any = a[sortField];
        let valB: any = b[sortField];

        if (sortField === "recommended_ring") {
          valA = RING_WEIGHT[a.recommended_ring] ?? 0;
          valB = RING_WEIGHT[b.recommended_ring] ?? 0;
        } else if (sortField === "lifecycle_stage") {
          valA = STAGE_WEIGHT[a.lifecycle_stage] ?? 0;
          valB = STAGE_WEIGHT[b.lifecycle_stage] ?? 0;
        } else if (sortField === "track") {
          valA = a.track || "testing";
          valB = b.track || "testing";
        } else if (sortField === "topic_name") {
          valA = a.topic_name || "";
          valB = b.topic_name || "";
        }

        if (typeof valA === "number" && typeof valB === "number") {
          return sortOrder === "asc" ? valA - valB : valB - valA;
        }

        const strA = String(valA ?? "").toLowerCase();
        const strB = String(valB ?? "").toLowerCase();
        const cmp = strA.localeCompare(strB);
        return sortOrder === "asc" ? cmp : -cmp;
      });
    }

    return result;
  }, [items, filters, sortField, sortOrder]);

  const renderSortIcon = (field: SortField) => {
    if (sortField !== field || !sortOrder) {
      return <span className="text-slate-600 ml-1 font-normal opacity-0 group-hover:opacity-100 transition-opacity">↕</span>;
    }
    return (
      <span className="text-blue-400 ml-1 font-bold">
        {sortOrder === "asc" ? "▲" : "▼"}
      </span>
    );
  };

  return (
    <div className="bg-[#121826] border border-[#1f293d] rounded-xl overflow-hidden shadow-2xl w-full">
      {/* Table Toolbar if column filters are active */}
      <div className="px-6 py-2.5 bg-[#0f1523] border-b border-[#1f293d] flex justify-between items-center text-xs text-slate-400">
        <div>
          Showing <span className="font-semibold text-slate-200">{processedItems.length}</span> of{" "}
          <span className="font-semibold text-slate-200">{items.length}</span> items
          {sortField && (
            <span className="ml-3 text-slate-400">
              Sorted by <span className="text-blue-300 font-semibold">{sortField}</span> ({sortOrder})
            </span>
          )}
        </div>
        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="text-[11px] text-blue-400 hover:text-blue-300 underline font-semibold cursor-pointer"
          >
            Reset Column Filters
          </button>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-[#161f33] text-xs uppercase text-slate-400 font-semibold tracking-wider select-none">
            {/* Header Labels (Clickable for Sorting) */}
            <tr>
              <th
                onClick={() => handleSort("track")}
                className="px-5 py-3.5 cursor-pointer hover:text-slate-200 transition-colors group"
              >
                <div className="flex items-center">
                  Track {renderSortIcon("track")}
                </div>
              </th>
              <th
                onClick={() => handleSort("name")}
                className="px-5 py-3.5 cursor-pointer hover:text-slate-200 transition-colors group"
              >
                <div className="flex items-center">
                  Trend / Innovation {renderSortIcon("name")}
                </div>
              </th>
              <th
                onClick={() => handleSort("topic_name")}
                className="px-5 py-3.5 cursor-pointer hover:text-slate-200 transition-colors group"
              >
                <div className="flex items-center">
                  Dynamic Theme {renderSortIcon("topic_name")}
                </div>
              </th>
              <th
                onClick={() => handleSort("category")}
                className="px-5 py-3.5 cursor-pointer hover:text-slate-200 transition-colors group"
              >
                <div className="flex items-center">
                  Pillar {renderSortIcon("category")}
                </div>
              </th>
              <th
                onClick={() => handleSort("recommended_ring")}
                className="px-5 py-3.5 cursor-pointer hover:text-slate-200 transition-colors group"
              >
                <div className="flex items-center">
                  Ring {renderSortIcon("recommended_ring")}
                </div>
              </th>
              <th
                onClick={() => handleSort("lifecycle_stage")}
                className="px-5 py-3.5 text-center cursor-pointer hover:text-slate-200 transition-colors group"
              >
                <div className="flex items-center justify-center">
                  Trajectory {renderSortIcon("lifecycle_stage")}
                </div>
              </th>
              <th
                onClick={() => handleSort("corroboration_count")}
                className="px-5 py-3.5 text-center cursor-pointer hover:text-slate-200 transition-colors group"
              >
                <div className="flex items-center justify-center">
                  Corroboration {renderSortIcon("corroboration_count")}
                </div>
              </th>
              <th
                onClick={() => handleSort("viability_score")}
                className="px-5 py-3.5 text-center cursor-pointer hover:text-slate-200 transition-colors group"
              >
                <div className="flex items-center justify-center">
                  Viability {renderSortIcon("viability_score")}
                </div>
              </th>
              <th
                onClick={() => handleSort("hype_score")}
                className="px-5 py-3.5 text-center cursor-pointer hover:text-slate-200 transition-colors group"
              >
                <div className="flex items-center justify-center">
                  Hype {renderSortIcon("hype_score")}
                </div>
              </th>
              <th
                onClick={() => handleSort("evidence_tier")}
                className="px-5 py-3.5 cursor-pointer hover:text-slate-200 transition-colors group"
              >
                <div className="flex items-center">
                  Evidence Tier {renderSortIcon("evidence_tier")}
                </div>
              </th>
            </tr>

            {/* Filter Input Row */}
            <tr className="bg-[#111726] border-y border-[#1f293d]">
              {/* Track filter */}
              <th className="px-3 py-2 font-normal">
                <select
                  value={filters.track}
                  onChange={(e) => handleFilterChange("track", e.target.value)}
                  className="w-full bg-[#0b0f19] border border-[#1f293d] rounded px-2 py-1 text-[11px] text-slate-300 focus:outline-none focus:border-blue-500"
                >
                  <option value="all">All Tracks</option>
                  <option value="testing">Software Testing</option>
                  <option value="evaluation">AI Evaluation</option>
                </select>
              </th>

              {/* Name filter */}
              <th className="px-3 py-2 font-normal">
                <input
                  type="text"
                  placeholder="Filter name..."
                  value={filters.name}
                  onChange={(e) => handleFilterChange("name", e.target.value)}
                  className="w-full bg-[#0b0f19] border border-[#1f293d] rounded px-2 py-1 text-[11px] text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500"
                />
              </th>

              {/* Dynamic Theme filter */}
              <th className="px-3 py-2 font-normal">
                <select
                  value={filters.theme}
                  onChange={(e) => handleFilterChange("theme", e.target.value)}
                  className="w-full bg-[#0b0f19] border border-[#1f293d] rounded px-2 py-1 text-[11px] text-slate-300 focus:outline-none focus:border-blue-500"
                >
                  <option value="all">All Themes</option>
                  {uniqueThemes.map((th) => (
                    <option key={th} value={th}>
                      {th}
                    </option>
                  ))}
                </select>
              </th>

              {/* Pillar filter */}
              <th className="px-3 py-2 font-normal">
                <select
                  value={filters.category}
                  onChange={(e) => handleFilterChange("category", e.target.value)}
                  className="w-full bg-[#0b0f19] border border-[#1f293d] rounded px-2 py-1 text-[11px] text-slate-300 focus:outline-none focus:border-blue-500"
                >
                  <option value="all">All Pillars</option>
                  {uniqueCategories.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </th>

              {/* Ring filter */}
              <th className="px-3 py-2 font-normal">
                <select
                  value={filters.ring}
                  onChange={(e) => handleFilterChange("ring", e.target.value)}
                  className="w-full bg-[#0b0f19] border border-[#1f293d] rounded px-2 py-1 text-[11px] text-slate-300 focus:outline-none focus:border-blue-500"
                >
                  <option value="all">All Rings</option>
                  <option value="Adopt">Adopt</option>
                  <option value="Trial">Trial</option>
                  <option value="Assess">Assess</option>
                  <option value="Hold">Hold</option>
                </select>
              </th>

              {/* Trajectory filter */}
              <th className="px-3 py-2 font-normal">
                <select
                  value={filters.stage}
                  onChange={(e) => handleFilterChange("stage", e.target.value)}
                  className="w-full bg-[#0b0f19] border border-[#1f293d] rounded px-2 py-1 text-[11px] text-slate-300 focus:outline-none focus:border-blue-500"
                >
                  <option value="all">All</option>
                  <option value="Consolidated">Consolidated</option>
                  <option value="Emerging">Emerging</option>
                  <option value="Fading">Fading</option>
                </select>
              </th>

              {/* Corroboration / Viability / Hype - no direct dropdowns, leave compact spacer */}
              <th className="px-3 py-2 text-center text-slate-600 font-mono text-[10px]">—</th>
              <th className="px-3 py-2 text-center text-slate-600 font-mono text-[10px]">—</th>
              <th className="px-3 py-2 text-center text-slate-600 font-mono text-[10px]">—</th>

              {/* Evidence Tier filter */}
              <th className="px-3 py-2 font-normal">
                <select
                  value={filters.tier}
                  onChange={(e) => handleFilterChange("tier", e.target.value)}
                  className="w-full bg-[#0b0f19] border border-[#1f293d] rounded px-2 py-1 text-[11px] text-slate-300 focus:outline-none focus:border-blue-500"
                >
                  <option value="all">All Tiers</option>
                  {uniqueTiers.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1f293d]">
            {processedItems.length === 0 ? (
              <tr>
                <td colSpan={10} className="px-6 py-8 text-center text-slate-500 text-sm">
                  No radar items match the active column filters.
                </td>
              </tr>
            ) : (
              processedItems.map((item) => {
                const isSelected = selectedItem?.id === item.id;
                const ringColor =
                  item.recommended_ring === "Adopt"
                    ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                    : item.recommended_ring === "Trial"
                    ? "bg-blue-500/20 text-blue-400 border-blue-500/30"
                    : item.recommended_ring === "Assess"
                    ? "bg-amber-500/20 text-amber-400 border-amber-500/30"
                    : "bg-red-500/20 text-red-400 border-red-500/30";

                const trajColor =
                  item.lifecycle_stage === "Emerging"
                    ? "text-sky-400 bg-sky-950/30 border-sky-500/30"
                    : item.lifecycle_stage === "Consolidated"
                    ? "text-emerald-400 bg-emerald-950/30 border-emerald-500/30"
                    : "text-rose-400 bg-rose-950/30 border-rose-500/30";

                return (
                  <tr
                    key={item.id}
                    onClick={() => onSelectItem(item)}
                    className={`cursor-pointer transition-colors ${
                      isSelected ? "bg-blue-900/20" : "hover:bg-[#1a233a]"
                    }`}
                  >
                    <td className="px-5 py-3.5 text-xs whitespace-nowrap">
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${
                          item.track === "evaluation"
                            ? "bg-purple-950/40 text-purple-300 border-purple-600/30"
                            : "bg-blue-950/40 text-blue-300 border-blue-600/30"
                        }`}
                      >
                        {item.track === "evaluation" ? "AI Evaluation" : "Software Testing"}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 font-semibold text-slate-100">{item.name}</td>
                    <td className="px-5 py-3.5 text-xs">
                      {item.topic_name ? (
                        <span
                          onClick={(e) => {
                            e.stopPropagation();
                            if (onSelectTheme) {
                              onSelectTheme(
                                selectedTheme === item.topic_name
                                  ? null
                                  : item.topic_name || null
                              );
                            }
                          }}
                          className={`inline-block px-2.5 py-1 rounded-md text-[11px] font-medium border transition-colors ${
                            selectedTheme === item.topic_name
                              ? "bg-purple-900/50 text-purple-200 border-purple-400"
                              : "bg-purple-950/30 text-purple-300 border-purple-500/30 hover:border-purple-400"
                          }`}
                          title="Click to filter by dynamic theme"
                        >
                          {item.topic_name}
                        </span>
                      ) : (
                        <span className="text-slate-500 italic text-[11px]">Independent</span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-xs">{item.category}</td>
                    <td className="px-5 py-3.5">
                      <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${ringColor}`}>
                        {item.recommended_ring}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-center">
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-md border ${trajColor}`}>
                        {item.lifecycle_stage}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-center font-mono">
                      <span className="px-2 py-0.5 rounded bg-[#161f33] text-blue-300 font-semibold text-xs border border-[#1f293d]">
                        {item.corroboration_count} {item.corroboration_count === 1 ? "source" : "sources"}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-center font-mono text-emerald-400">
                      {(item.viability_score * 100).toFixed(0)}%
                    </td>
                    <td className="px-5 py-3.5 text-center font-mono text-amber-400">
                      {(item.hype_score * 100).toFixed(0)}%
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-400">{item.evidence_tier}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
