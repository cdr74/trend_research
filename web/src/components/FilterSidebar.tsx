import React from "react";
import { RadarRing, QECategory, EvidenceTier } from "../types";

interface FilterSidebarProps {
  selectedRings: Set<RadarRing>;
  onToggleRing: (ring: RadarRing) => void;
  selectedCategories: Set<QECategory>;
  onToggleCategory: (cat: QECategory) => void;
  selectedEvidenceTiers: Set<EvidenceTier>;
  onToggleEvidenceTier: (tier: EvidenceTier) => void;
  minViability: number;
  onChangeMinViability: (val: number) => void;
  maxHype: number;
  onChangeMaxHype: (val: number) => void;
  searchTerm: string;
  onChangeSearchTerm: (term: string) => void;
  onResetFilters: () => void;
  availableThemes?: string[];
  selectedTheme?: string | null;
  onSelectTheme?: (theme: string | null) => void;
}

const ALL_RINGS: RadarRing[] = ["Adopt", "Trial", "Assess", "Hold"];
const ALL_CATEGORIES: QECategory[] = [
  "Spec & Model",
  "Test Synthesis",
  "Execution & Optimization",
  "Triage & Self-Healing",
  "Agent Systems",
  "Governance & Evals",
];
const ALL_TIERS: EvidenceTier[] = [
  "Academic Peer-Reviewed",
  "Open Source Repo",
  "Engineering Post-Mortem",
  "Vendor Announcement",
];

export const FilterSidebar: React.FC<FilterSidebarProps> = ({
  selectedRings,
  onToggleRing,
  selectedCategories,
  onToggleCategory,
  selectedEvidenceTiers,
  onToggleEvidenceTier,
  minViability,
  onChangeMinViability,
  maxHype,
  onChangeMaxHype,
  searchTerm,
  onChangeSearchTerm,
  onResetFilters,
  availableThemes = [],
  selectedTheme = null,
  onSelectTheme,
}) => {
  return (
    <div className="w-80 bg-[#121826] border border-[#1f293d] rounded-xl p-5 shadow-2xl space-y-6">
      {/* Search Omnibar */}
      <div>
        <div className="flex justify-between items-center mb-1.5">
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
            Search Omnibar
          </label>
          <button
            onClick={onResetFilters}
            className="text-[10px] text-blue-400 hover:text-blue-300 font-semibold underline"
          >
            Reset All
          </button>
        </div>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => onChangeSearchTerm(e.target.value)}
          placeholder='e.g. theme:mutation ring:Adopt viability:>0.8'
          className="w-full bg-[#0b0f19] border border-[#1f293d] rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
        />
        <p className="text-[10px] text-slate-500 mt-1 leading-tight">
          Supports: <code className="text-slate-400">theme:</code>, <code className="text-slate-400">track:</code>, <code className="text-slate-400">ring:</code>, <code className="text-slate-400">pillar:</code>, <code className="text-slate-400">viability:&gt;0.8</code>
        </p>
      </div>

      {/* Dynamic Themes */}
      {availableThemes.length > 0 && (
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
              Dynamic Themes ({availableThemes.length})
            </label>
            {selectedTheme && (
              <button
                onClick={() => onSelectTheme && onSelectTheme(null)}
                className="text-[10px] text-purple-400 hover:text-purple-300 font-semibold underline"
              >
                Clear Theme
              </button>
            )}
          </div>
          <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
            {availableThemes.map((theme) => {
              const active = selectedTheme === theme;
              return (
                <button
                  key={theme}
                  onClick={() => onSelectTheme && onSelectTheme(active ? null : theme)}
                  className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    active
                      ? "bg-purple-600/30 text-purple-200 border border-purple-500/50 shadow-sm"
                      : "text-slate-400 hover:bg-[#161f33] border border-transparent"
                  }`}
                >
                  <div className="truncate">{theme}</div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Ring Filter */}
      <div>
        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
          Radar Rings
        </label>
        <div className="grid grid-cols-2 gap-2">
          {ALL_RINGS.map((ring) => {
            const active = selectedRings.has(ring);
            const borderCol =
              ring === "Adopt"
                ? "border-emerald-500 text-emerald-400"
                : ring === "Trial"
                ? "border-blue-500 text-blue-400"
                : ring === "Assess"
                ? "border-amber-500 text-amber-400"
                : "border-red-500 text-red-400";

            return (
              <button
                key={ring}
                onClick={() => onToggleRing(ring)}
                className={`px-3 py-2 rounded-lg text-xs font-semibold border transition-all ${
                  active
                    ? `${borderCol} bg-[#1a233a]`
                    : "border-[#1f293d] text-slate-500 hover:text-slate-300"
                }`}
              >
                {ring}
              </button>
            );
          })}
        </div>
      </div>

      {/* Score Range Sliders */}
      <div className="space-y-4">
        <div>
          <div className="flex justify-between text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
            <span>Min Enterprise Viability</span>
            <span className="font-mono text-emerald-400">{(minViability * 100).toFixed(0)}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={minViability}
            onChange={(e) => onChangeMinViability(parseFloat(e.target.value))}
            className="w-full accent-emerald-500 cursor-pointer"
          />
        </div>

        <div>
          <div className="flex justify-between text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
            <span>Max Anti-Hype Ceiling</span>
            <span className="font-mono text-amber-400">{(maxHype * 100).toFixed(0)}%</span>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={maxHype}
            onChange={(e) => onChangeMaxHype(parseFloat(e.target.value))}
            className="w-full accent-amber-500 cursor-pointer"
          />
        </div>
      </div>

      {/* Categories Filter */}
      <div>
        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
          QE Pillars
        </label>
        <div className="space-y-1.5">
          {ALL_CATEGORIES.map((cat) => {
            const active = selectedCategories.has(cat);
            return (
              <button
                key={cat}
                onClick={() => onToggleCategory(cat)}
                className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                  active
                    ? "bg-blue-600/20 text-blue-300 border border-blue-500/30"
                    : "text-slate-400 hover:bg-[#161f33] border border-transparent"
                }`}
              >
                {cat}
              </button>
            );
          })}
        </div>
      </div>

      {/* Evidence Tier */}
      <div>
        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
          Evidence Tier
        </label>
        <div className="space-y-1">
          {ALL_TIERS.map((tier) => {
            const active = selectedEvidenceTiers.has(tier);
            return (
              <label key={tier} className="flex items-center space-x-2 text-xs text-slate-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={active}
                  onChange={() => onToggleEvidenceTier(tier)}
                  className="rounded border-[#1f293d] text-blue-600 focus:ring-0"
                />
                <span>{tier}</span>
              </label>
            );
          })}
        </div>
      </div>
    </div>
  );
};
