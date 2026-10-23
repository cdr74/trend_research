import React from "react";
import { RadarItem, RadarRing, QECategory } from "../types";

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

export const RadarChart: React.FC<RadarChartProps> = ({ items, selectedItem, onSelectItem }) => {
  const size = 800;
  const center = size / 2;

  // Calculate position of a blip deterministically from category and ring
  const getBlipPosition = (item: RadarItem, index: number) => {
    const catIndex = CATEGORIES.indexOf(item.category);
    const sliceAngle = (2 * Math.PI) / CATEGORIES.length;
    const baseAngle = catIndex * sliceAngle + sliceAngle / 2;

    const ringCfg = RING_CONFIG[item.recommended_ring];
    const prevRadius =
      item.recommended_ring === "Adopt"
        ? 30
        : item.recommended_ring === "Trial"
        ? 110
        : item.recommended_ring === "Assess"
        ? 200
        : 290;

    // Distribute within ring band
    const bandWidth = ringCfg.radius - prevRadius;
    const r = prevRadius + bandWidth * 0.25 + ((index * 37) % (bandWidth * 0.5));
    const angleOffset = (((index * 17) % 30) - 15) * (Math.PI / 180);
    const angle = baseAngle + angleOffset;

    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    };
  };

  return (
    <div className="relative flex justify-center items-center bg-[#121826] border border-[#1f293d] rounded-xl p-6 shadow-2xl overflow-hidden">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="max-w-full h-auto">
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

        {/* Category dividing axes */}
        {CATEGORIES.map((cat, i) => {
          const angle = i * ((2 * Math.PI) / CATEGORIES.length);
          const x2 = center + 390 * Math.cos(angle);
          const y2 = center + 390 * Math.sin(angle);

          const labelAngle = angle + (Math.PI / CATEGORIES.length);
          const lx = center + 400 * Math.cos(labelAngle);
          const ly = center + 400 * Math.sin(labelAngle);

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
                fontSize="11"
                fontWeight="600"
                textAnchor={lx > center + 20 ? "start" : lx < center - 20 ? "end" : "middle"}
                dominantBaseline="central"
              >
                {cat}
              </text>
            </g>
          );
        })}

        {/* Blips */}
        {items.map((item, idx) => {
          const pos = getBlipPosition(item, idx);
          const isSelected = selectedItem?.id === item.id;
          const color = RING_CONFIG[item.recommended_ring].color;

          return (
            <g
              key={item.id}
              className="cursor-pointer transition-transform hover:scale-125"
              onClick={() => onSelectItem(item)}
            >
              {isSelected && (
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r="14"
                  fill="none"
                  stroke={color}
                  strokeWidth="2"
                  className="animate-ping opacity-75"
                />
              )}
              <circle
                cx={pos.x}
                cy={pos.y}
                r={isSelected ? "9" : "7"}
                fill={color}
                stroke="#0b0f19"
                strokeWidth="2"
              />
              <text
                x={pos.x}
                y={pos.y - 12}
                fill="#f1f5f9"
                fontSize="10"
                fontWeight="600"
                textAnchor="middle"
                className="pointer-events-none drop-shadow-md"
              >
                {item.name}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
