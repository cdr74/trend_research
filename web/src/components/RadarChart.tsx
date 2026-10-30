import React, { useState } from "react";
import { RadarItem, RadarRing, QECategory } from "../types";
import { useZoomPan } from "../hooks/useZoomPan";
import { ZoomControls } from "./ZoomControls";

interface RadarChartProps {
  items: RadarItem[];
  selectedItem: RadarItem | null;
  onSelectItem: (item: RadarItem) => void;
}

const RING_CONFIG: Record<RadarRing, { radius: number; color: string; label: string }> = {
  Adopt: { radius: 110, color: "#10b981", label: "ADOPT" },
  Trial: { radius: 200, color: "#3b82f6", label: "TRIAL" },
  Assess: { radius: 290, color: "#f59e0b", label: "ASSESS" },
  Hold: { radius: 370, color: "#ef4444", label: "HOLD" },
};

const CATEGORIES: QECategory[] = [
  "Spec & Model",
  "Test Synthesis",
  "Execution & Optimization",
  "Triage & Self-Healing",
  "Agent Systems",
  "Governance & Evals",
];

// Invariant 32-bit FNV-1a hash to guarantee static spatial placement per item
const getItemHash = (id: string): number => {
  let hash = 2166136261;
  for (let i = 0; i < id.length; i++) {
    hash ^= id.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
};

export const RadarChart: React.FC<RadarChartProps> = ({ items, selectedItem, onSelectItem }) => {
  const size = 800;
  const center = size / 2;
  const [hoveredItem, setHoveredItem] = useState<RadarItem | null>(null);

  const {
    svgRef,
    transform,
    zoomIn,
    zoomOut,
    resetZoom,
    hasDraggedRef,
    handlers,
  } = useZoomPan({ minZoom: 0.6, maxZoom: 6.0 });

  // Calculate position of a blip deterministically from item identity (100% stable across filter toggles)
  const getBlipPosition = (item: RadarItem) => {
    const catIndex = CATEGORIES.indexOf(item.category);
    const validCatIndex = catIndex >= 0 ? catIndex : 0;
    const sliceAngle = (2 * Math.PI) / CATEGORIES.length;
    const baseAngle = validCatIndex * sliceAngle + sliceAngle / 2;

    const ringCfg = RING_CONFIG[item.recommended_ring];
    const prevRadius =
      item.recommended_ring === "Adopt"
        ? 35
        : item.recommended_ring === "Trial"
        ? 110
        : item.recommended_ring === "Assess"
        ? 200
        : 290;

    const hash = getItemHash(item.id || item.name);
    const bandWidth = ringCfg.radius - prevRadius;
    const rRatio = 0.20 + ((hash % 1000) / 1000.0) * 0.60;
    const r = prevRadius + bandWidth * rRatio;

    // Angle offset: spread within +/- 18 degrees of slice center
    const angleOffset = ((((hash >> 8) % 360) / 10.0) - 18.0) * (Math.PI / 180.0);
    const angle = baseAngle + angleOffset;

    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    };
  };

  const hoveredPos = hoveredItem ? getBlipPosition(hoveredItem) : null;
  const scalePow = Math.pow(transform.k, 0.45);

  return (
    <div className="relative flex justify-center items-center bg-[#121826] border border-[#1f293d] rounded-2xl p-6 shadow-2xl overflow-hidden select-none">
      {/* Interactive SVG with cursor feedback */}
      <svg
        ref={svgRef}
        {...handlers}
        width={size}
        height={size}
        viewBox="-65 -65 930 930"
        className="max-w-full h-auto cursor-grab active:cursor-grabbing"
      >
        <g transform={`translate(${transform.x}, ${transform.y}) scale(${transform.k})`}>
          {/* Background Concentric Rings */}
          {(Object.keys(RING_CONFIG) as RadarRing[]).reverse().map((ring) => {
            const cfg = RING_CONFIG[ring];
            return (
              <g key={ring}>
                <circle
                  cx={center}
                  cy={center}
                  r={cfg.radius}
                  fill="none"
                  stroke="#1f293d"
                  strokeWidth="1.5"
                  strokeDasharray={ring === "Hold" ? "4 4" : "none"}
                />
                <text
                  x={center}
                  y={center - cfg.radius + 18}
                  fill={cfg.color}
                  fontSize="11"
                  fontWeight="700"
                  letterSpacing="0.1em"
                  textAnchor="middle"
                  opacity="0.8"
                >
                  {cfg.label}
                </text>
              </g>
            );
          })}

          {/* Category dividing axes & un-clipped boundary labels */}
          {CATEGORIES.map((cat, i) => {
            const angle = i * ((2 * Math.PI) / CATEGORIES.length);
            const x2 = center + 380 * Math.cos(angle);
            const y2 = center + 380 * Math.sin(angle);

            const labelAngle = angle + Math.PI / CATEGORIES.length;
            const lx = center + 415 * Math.cos(labelAngle);
            const ly = center + 415 * Math.sin(labelAngle);

            // Dynamic typography anchors based on circular position
            const dominantBaseline =
              ly < center - 120 ? "auto" : ly > center + 120 ? "hanging" : "central";
            const textAnchor =
              lx > center + 50 ? "start" : lx < center - 50 ? "end" : "middle";

            return (
              <g key={cat}>
                <line
                  x1={center}
                  y1={center}
                  x2={x2}
                  y2={y2}
                  stroke="#1f293d"
                  strokeWidth="1.5"
                />
                <text
                  x={lx}
                  y={ly}
                  fill="#94a3b8"
                  fontSize="12"
                  fontWeight="600"
                  textAnchor={textAnchor}
                  dominantBaseline={dominantBaseline}
                  className="select-none"
                >
                  {cat}
                </text>
              </g>
            );
          })}

          {/* Blips (with scale-invariant radius and typography) */}
          {items.map((item) => {
            const pos = getBlipPosition(item);
            const isSelected = selectedItem?.id === item.id;
            const isHovered = hoveredItem?.id === item.id;
            const color = RING_CONFIG[item.recommended_ring].color;

            // Inversely scale blip circle and text slightly so zoomed clusters stay readable
            const baseRadius = isSelected || isHovered ? 8.5 : 6.5;
            const blipRadius = Math.max(3.5, baseRadius / scalePow);
            const haloRadius = Math.max(8.0, 16 / scalePow);
            const fontSize = Math.max(7.5, (isSelected || isHovered ? 11 : 9.5) / scalePow);
            const textOffset = Math.max(8, 12 / scalePow);

            return (
              <g
                key={item.id}
                className="cursor-pointer"
                onClick={(e) => {
                  e.stopPropagation();
                  if (hasDraggedRef.current) return;
                  onSelectItem(item);
                }}
                onMouseEnter={() => setHoveredItem(item)}
                onMouseLeave={() => setHoveredItem(null)}
              >
                {/* Soft ambient halo on hover or selection */}
                {(isSelected || isHovered) && (
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r={haloRadius}
                    fill={color}
                    fillOpacity="0.25"
                    className="pointer-events-none animate-pulse"
                  />
                )}
                {isSelected && (
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r={haloRadius * 1.15}
                    fill="none"
                    stroke={color}
                    strokeWidth="1.5"
                    className="pointer-events-none animate-ping opacity-75"
                  />
                )}
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={blipRadius}
                  fill={color}
                  stroke="#0b0f19"
                  strokeWidth="1.5"
                  className="transition-all duration-150"
                />
                <text
                  x={pos.x}
                  y={pos.y - textOffset}
                  fill={isSelected || isHovered ? "#ffffff" : "#cbd5e1"}
                  fontSize={fontSize}
                  fontWeight={isSelected || isHovered ? "700" : "600"}
                  textAnchor="middle"
                  className="pointer-events-none drop-shadow-md select-none transition-colors duration-150"
                >
                  {item.name}
                </text>
              </g>
            );
          })}
        </g>
      </svg>

      {/* Floating Pan/Zoom HUD Controls */}
      <ZoomControls
        zoomLevel={transform.k}
        onZoomIn={zoomIn}
        onZoomOut={zoomOut}
        onReset={resetZoom}
      />

      {/* Floating Tooltip mapped through active transform */}
      {hoveredItem && hoveredPos && (
        <div
          className="absolute z-50 bg-[#1e293b] border border-slate-700 text-slate-100 rounded-xl p-3 shadow-2xl pointer-events-none max-w-xs transition-opacity duration-150"
          style={{
            left: Math.min(
              Math.max(hoveredPos.x * transform.k + transform.x - 60, 20),
              size - 240
            ),
            top: Math.max(hoveredPos.y * transform.k + transform.y - 95, 20),
          }}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="font-bold text-xs text-white">{hoveredItem.name}</span>
            <span
              className="text-[10px] font-semibold px-1.5 py-0.5 rounded"
              style={{
                backgroundColor: `${RING_CONFIG[hoveredItem.recommended_ring].color}20`,
                color: RING_CONFIG[hoveredItem.recommended_ring].color,
              }}
            >
              {hoveredItem.recommended_ring}
            </span>
          </div>
          <div className="text-[11px] text-slate-400 mb-1.5 line-clamp-2">
            {hoveredItem.key_innovation}
          </div>
          <div className="flex justify-between text-[10px] text-slate-400 border-t border-slate-700/60 pt-1">
            <span>
              Viability:{" "}
              <strong className="text-emerald-400">
                {hoveredItem.viability_score.toFixed(2)}
              </strong>
            </span>
            <span>
              Hype:{" "}
              <strong className="text-amber-400">
                {hoveredItem.hype_score.toFixed(2)}
              </strong>
            </span>
            <span>
              Corrob: <strong>{hoveredItem.corroboration_count}x</strong>
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
