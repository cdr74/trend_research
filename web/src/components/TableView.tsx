import React from "react";
import { RadarItem } from "../types";

interface TableViewProps {
  items: RadarItem[];
  selectedItem: RadarItem | null;
  onSelectItem: (item: RadarItem) => void;
  selectedTheme?: string | null;
  onSelectTheme?: (theme: string | null) => void;
}

export const TableView: React.FC<TableViewProps> = ({
  items,
  selectedItem,
  onSelectItem,
  selectedTheme,
  onSelectTheme,
}) => {
  return (
    <div className="bg-[#121826] border border-[#1f293d] rounded-xl overflow-hidden shadow-2xl">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-[#161f33] text-xs uppercase text-slate-400 font-semibold tracking-wider">
            <tr>
              <th className="px-6 py-4">Track</th>
              <th className="px-6 py-4">Trend / Innovation</th>
              <th className="px-6 py-4">Dynamic Theme</th>
              <th className="px-6 py-4">Pillar</th>
              <th className="px-6 py-4">Ring</th>
              <th className="px-6 py-4 text-center">Trajectory</th>
              <th className="px-6 py-4 text-center">Corroboration</th>
              <th className="px-6 py-4 text-center">Viability</th>
              <th className="px-6 py-4 text-center">Hype</th>
              <th className="px-6 py-4">Evidence Tier</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1f293d]">
            {items.map((item) => {
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
                  <td className="px-6 py-4 text-xs whitespace-nowrap">
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
                  <td className="px-6 py-4 font-semibold text-slate-100">{item.name}</td>
                  <td className="px-6 py-4 text-xs">
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
                  <td className="px-6 py-4 text-xs">{item.category}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${ringColor}`}>
                      {item.recommended_ring}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`px-2 py-0.5 text-xs font-medium rounded-md border ${trajColor}`}>
                      {item.lifecycle_stage}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center font-mono">
                    <span className="px-2 py-0.5 rounded bg-[#161f33] text-blue-300 font-semibold text-xs border border-[#1f293d]">
                      {item.corroboration_count} {item.corroboration_count === 1 ? "source" : "sources"}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center font-mono text-emerald-400">
                    {(item.viability_score * 100).toFixed(0)}%
                  </td>
                  <td className="px-6 py-4 text-center font-mono text-amber-400">
                    {(item.hype_score * 100).toFixed(0)}%
                  </td>
                  <td className="px-6 py-4 text-xs text-slate-400">{item.evidence_tier}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
