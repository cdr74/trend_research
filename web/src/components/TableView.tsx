import React from "react";
import { RadarItem } from "../types";

interface TableViewProps {
  items: RadarItem[];
  selectedItem: RadarItem | null;
  onSelectItem: (item: RadarItem) => void;
}

export const TableView: React.FC<TableViewProps> = ({ items, selectedItem, onSelectItem }) => {
  return (
    <div className="bg-[#121826] border border-[#1f293d] rounded-xl overflow-hidden shadow-2xl">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-[#161f33] text-xs uppercase text-slate-400 font-semibold tracking-wider">
            <tr>
              <th className="px-6 py-4">Tool / Paper</th>
              <th className="px-6 py-4">Category</th>
              <th className="px-6 py-4">Ring</th>
              <th className="px-6 py-4 text-center">Viability</th>
              <th className="px-6 py-4 text-center">Hype</th>
              <th className="px-6 py-4">Evidence Tier</th>
              <th className="px-6 py-4">Key Innovation</th>
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

              return (
                <tr
                  key={item.id}
                  onClick={() => onSelectItem(item)}
                  className={`cursor-pointer transition-colors ${
                    isSelected ? "bg-blue-900/20" : "hover:bg-[#1a233a]"
                  }`}
                >
                  <td className="px-6 py-4 font-semibold text-slate-100">{item.name}</td>
                  <td className="px-6 py-4">{item.category}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${ringColor}`}>
                      {item.recommended_ring}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center font-mono text-emerald-400">
                    {(item.viability_score * 100).toFixed(0)}%
                  </td>
                  <td className="px-6 py-4 text-center font-mono text-amber-400">
                    {(item.hype_score * 100).toFixed(0)}%
                  </td>
                  <td className="px-6 py-4 text-xs text-slate-400">{item.evidence_tier}</td>
                  <td className="px-6 py-4 text-xs text-slate-300 max-w-xs truncate">
                    {item.key_innovation}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
