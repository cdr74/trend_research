import React, { useState } from "react";
import { RadarItem, RadarRing } from "../types";

interface ScatterPlotProps {
  items: RadarItem[];
  selectedItem: RadarItem | null;
  onSelectItem: (item: RadarItem) => void;
}

const RING_COLORS: Record<RadarRing, string> = {
  Adopt: "#10b981", // emerald
  Trial: "#3b82f6", // blue
  Assess: "#f59e0b", // amber
  Hold: "#ef4444", // rose
};

export const ScatterPlot: React.FC<ScatterPlotProps> = ({
  items,
  selectedItem,
  onSelectItem,
}) => {
  const [hoveredItem, setHoveredItem] = useState<RadarItem | null>(null);

  // SVG dimensions
  const width = 760;
  const height = 560;
  const padding = 70;

  const innerWidth = width - padding * 2;
  const innerHeight = height - padding * 2;

  // Scale functions: X is Hype (0 to 1), Y is Viability (0 to 1)
  const getX = (hype: number) => padding + hype * innerWidth;
  const getY = (viability: number) => height - padding - viability * innerHeight;

  return (
    <div className="relative flex flex-col items-center select-none bg-[#121826] border border-[#1f293d] rounded-2xl p-6 shadow-2xl">
      <div className="w-full flex justify-between items-center mb-4 px-2">
        <div>
          <h2 className="text-sm font-semibold text-slate-200">
            Scatter Matrix: Viability vs. Hype
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Quadrant analysis identifying high-viability zero-hype innovations vs. marketing wrappers.
          </p>
        </div>
        <div className="flex items-center space-x-3 text-xs">
          {(["Adopt", "Trial", "Assess", "Hold"] as RadarRing[]).map((ring) => (
            <div key={ring} className="flex items-center space-x-1.5">
              <span
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: RING_COLORS[ring] }}
              />
              <span className="text-slate-300 font-medium">{ring}</span>
            </div>
          ))}
        </div>
      </div>

      <svg width={width} height={height} className="overflow-visible">
        {/* Quadrant Tint Backgrounds */}
        {/* Top-Left: Enterprise Sweet Spot (Low Hype, High Viability) */}
        <rect
          x={padding}
          y={padding}
          width={innerWidth * 0.4}
          height={innerHeight * 0.35}
          fill="#10b981"
          fillOpacity="0.05"
          rx="6"
        />
        <text
          x={padding + 10}
          y={padding + 22}
          fill="#10b981"
          fontSize="11"
          fontWeight="600"
          opacity="0.8"
        >
          ★ High Viability / Low Hype (Enterprise Sweet Spot)
        </text>

        {/* Bottom-Right: Marketing Traps & Wrappers (High Hype, Low Viability) */}
        <rect
          x={padding + innerWidth * 0.5}
          y={padding + innerHeight * 0.45}
          width={innerWidth * 0.5}
          height={innerHeight * 0.55}
          fill="#ef4444"
          fillOpacity="0.04"
          rx="6"
        />
        <text
          x={width - padding - 10}
          y={height - padding - 14}
          fill="#ef4444"
          fontSize="11"
          fontWeight="600"
          textAnchor="end"
          opacity="0.8"
        >
          ⚠ High Hype / Low Viability (Marketing Wrappers)
        </text>

        {/* Grid lines */}
        {[0.2, 0.4, 0.6, 0.8].map((val) => (
          <g key={val}>
            {/* Horizontal line (viability) */}
            <line
              x1={padding}
              y1={getY(val)}
              x2={width - padding}
              y2={getY(val)}
              stroke="#1f293d"
              strokeDasharray="4 4"
            />
            <text
              x={padding - 10}
              y={getY(val) + 4}
              fill="#64748b"
              fontSize="10"
              textAnchor="end"
            >
              {val.toFixed(1)}
            </text>

            {/* Vertical line (hype) */}
            <line
              x1={getX(val)}
              y1={padding}
              x2={getX(val)}
              y2={height - padding}
              stroke="#1f293d"
              strokeDasharray="4 4"
            />
            <text
              x={getX(val)}
              y={height - padding + 18}
              fill="#64748b"
              fontSize="10"
              textAnchor="middle"
            >
              {val.toFixed(1)}
            </text>
          </g>
        ))}

        {/* Main Axes */}
        <line
          x1={padding}
          y1={height - padding}
          x2={width - padding}
          y2={height - padding}
          stroke="#475569"
          strokeWidth="1.5"
        />
        <line
          x1={padding}
          y1={padding}
          x2={padding}
          y2={height - padding}
          stroke="#475569"
          strokeWidth="1.5"
        />

        {/* Axis Labels */}
        <text
          x={width / 2}
          y={height - 20}
          fill="#94a3b8"
          fontSize="12"
          fontWeight="600"
          textAnchor="middle"
        >
          Anti-Hype Score (0.0 = Verified Rigor, 1.0 = Pure Vanity/Marketing) →
        </text>
        <text
          x={-height / 2}
          y={22}
          fill="#94a3b8"
          fontSize="12"
          fontWeight="600"
          textAnchor="middle"
          transform="rotate(-90)"
        >
          Production Viability Score (0.0 → 1.0) →
        </text>

        {/* Data Points */}
        {items.map((item) => {
          const cx = getX(item.hype_score);
          const cy = getY(item.viability_score);
          const isSelected = selectedItem?.id === item.id;
          const isHovered = hoveredItem?.id === item.id;
          const color = RING_COLORS[item.recommended_ring] || "#94a3b8";

          return (
            <g
              key={item.id}
              className="cursor-pointer transition-transform duration-150"
              onClick={() => onSelectItem(item)}
              onMouseEnter={() => setHoveredItem(item)}
              onMouseLeave={() => setHoveredItem(null)}
            >
              {/* Pulse / halo if selected or hovered */}
              {(isSelected || isHovered) && (
                <circle
                  cx={cx}
                  cy={cy}
                  r="14"
                  fill={color}
                  fillOpacity="0.25"
                  className="animate-pulse"
                />
              )}
              <circle
                cx={cx}
                cy={cy}
                r={isSelected || isHovered ? "8" : "6"}
                fill={color}
                stroke="#0b0f19"
                strokeWidth="2"
                className="transition-all"
              />
              {/* Tool name label */}
              <text
                x={cx + 9}
                y={cy + 4}
                fill={isSelected || isHovered ? "#f8fafc" : "#94a3b8"}
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
            left: Math.min(Math.max(getX(hoveredItem.hype_score) - 40, 20), width - 200),
            top: Math.max(getY(hoveredItem.viability_score) - 80, 20),
          }}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="font-bold text-xs text-white">{hoveredItem.name}</span>
            <span
              className="text-[10px] font-semibold px-1.5 py-0.5 rounded"
              style={{
                backgroundColor: `${RING_COLORS[hoveredItem.recommended_ring]}20`,
                color: RING_COLORS[hoveredItem.recommended_ring],
              }}
            >
              {hoveredItem.recommended_ring}
            </span>
          </div>
          <div className="text-[11px] text-slate-400 mb-1.5 line-clamp-2">
            {hoveredItem.key_innovation}
          </div>
          <div className="flex justify-between text-[10px] text-slate-400 border-t border-slate-700/60 pt-1">
            <span>Viability: <strong className="text-emerald-400">{hoveredItem.viability_score.toFixed(2)}</strong></span>
            <span>Hype: <strong className="text-amber-400">{hoveredItem.hype_score.toFixed(2)}</strong></span>
            <span>Corrob: <strong>{hoveredItem.corroboration_count}x</strong></span>
          </div>
        </div>
      )}
    </div>
  );
};
