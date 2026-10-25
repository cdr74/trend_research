import React, { useState } from "react";
import { RadarItem, QECategory } from "../types";

interface ClusterMapProps {
  items: RadarItem[];
  selectedItem: RadarItem | null;
  onSelectItem: (item: RadarItem) => void;
}

const CATEGORY_COLORS: Record<QECategory, string> = {
  "Spec & Model": "#38bdf8", // sky
  "Test Synthesis": "#818cf8", // indigo
  "Execution & Optimization": "#34d399", // emerald
  "Triage & Self-Healing": "#fbbf24", // amber
  "Agent Systems": "#f472b6", // pink
  "Governance & Evals": "#a78bfa", // purple
};

export const ClusterMap: React.FC<ClusterMapProps> = ({
  items,
  selectedItem,
  onSelectItem,
}) => {
  const [hoveredItem, setHoveredItem] = useState<RadarItem | null>(null);

  const width = 760;
  const height = 560;
  const padding = 60;

  const innerWidth = width - padding * 2;
  const innerHeight = height - padding * 2;

  // Convert normalized [-1.0, 1.0] coordinate to canvas space
  const getCanvasCoords = (item: RadarItem, index: number): { x: number; y: number } => {
    let nx = item.cluster_x;
    let ny = item.cluster_y;

    // Fallback if coordinates missing: arrange in a deterministic circle
    if (nx === undefined || ny === undefined) {
      const angle = (index / Math.max(items.length, 1)) * 2 * Math.PI;
      nx = Math.cos(angle) * 0.7;
      ny = Math.sin(angle) * 0.7;
    }

    const x = padding + ((nx + 1.0) / 2.0) * innerWidth;
    const y = padding + ((ny + 1.0) / 2.0) * innerHeight;
    return { x, y };
  };

  return (
    <div className="relative flex flex-col items-center select-none bg-[#121826] border border-[#1f293d] rounded-2xl p-6 shadow-2xl">
      <div className="w-full flex justify-between items-center mb-4 px-2">
        <div>
          <h2 className="text-sm font-semibold text-slate-200">
            Semantic Cluster Map (UMAP 2D Projection)
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Manifold projection of 1536-dimensional embeddings. Closer distance indicates higher semantic & architectural overlap.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-[11px] max-w-sm justify-end">
          {Object.entries(CATEGORY_COLORS).map(([cat, color]) => (
            <div key={cat} className="flex items-center space-x-1.5 bg-[#1b2234] px-2 py-0.5 rounded-md border border-slate-700/50">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-slate-300 font-medium">{cat}</span>
            </div>
          ))}
        </div>
      </div>

      <svg width={width} height={height} className="overflow-visible bg-[#0d121f] rounded-xl border border-[#1f293d]/50">
        {/* Subtle coordinate grid lines */}
        <line x1={width / 2} y1={padding / 2} x2={width / 2} y2={height - padding / 2} stroke="#1e293b" strokeDasharray="3 3" />
        <line x1={padding / 2} y1={height / 2} x2={width - padding / 2} y2={height / 2} stroke="#1e293b" strokeDasharray="3 3" />

        {/* Semantic Nodes */}
        {items.map((item, idx) => {
          const { x, y } = getCanvasCoords(item, idx);
          const isSelected = selectedItem?.id === item.id;
          const isHovered = hoveredItem?.id === item.id;
          const color = CATEGORY_COLORS[item.category] || "#94a3b8";

          return (
            <g
              key={item.id}
              className="cursor-pointer transition-transform duration-150"
              onClick={() => onSelectItem(item)}
              onMouseEnter={() => setHoveredItem(item)}
              onMouseLeave={() => setHoveredItem(null)}
            >
              {(isSelected || isHovered) && (
                <circle
                  cx={x}
                  cy={y}
                  r="16"
                  fill={color}
                  fillOpacity="0.2"
                  className="animate-pulse"
                />
              )}
              <circle
                cx={x}
                cy={y}
                r={isSelected || isHovered ? "8" : "6"}
                fill={color}
                stroke="#0b0f19"
                strokeWidth="2"
              />
              <text
                x={x + 10}
                y={y + 4}
                fill={isSelected || isHovered ? "#ffffff" : "#94a3b8"}
                fontSize="10"
                fontWeight={isSelected || isHovered ? "700" : "500"}
                className="pointer-events-none"
              >
                {item.name}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Floating Tooltip */}
      {hoveredItem && (
        <div
          className="absolute z-50 bg-[#1e293b] border border-slate-700 text-slate-100 rounded-xl p-3 shadow-2xl pointer-events-none max-w-xs transition-opacity duration-150"
          style={{
            left: Math.min(Math.max(getCanvasCoords(hoveredItem, 0).x - 40, 20), width - 200),
            top: Math.max(getCanvasCoords(hoveredItem, 0).y - 80, 20),
          }}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="font-bold text-xs text-white">{hoveredItem.name}</span>
            <span className="text-[10px] font-semibold text-slate-300">
              {hoveredItem.category}
            </span>
          </div>
          <div className="text-[11px] text-slate-400 mb-1.5 line-clamp-2">
            {hoveredItem.key_innovation}
          </div>
          <div className="flex justify-between text-[10px] text-slate-400 border-t border-slate-700/60 pt-1">
            <span>Ring: <strong className="text-emerald-400">{hoveredItem.recommended_ring}</strong></span>
            <span>Viability: <strong className="text-blue-400">{hoveredItem.viability_score.toFixed(2)}</strong></span>
            <span>Coords: [{hoveredItem.cluster_x?.toFixed(2) ?? "0.00"}, {hoveredItem.cluster_y?.toFixed(2) ?? "0.00"}]</span>
          </div>
        </div>
      )}
    </div>
  );
};
