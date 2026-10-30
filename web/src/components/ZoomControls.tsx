import React from "react";
import { ZoomIn, ZoomOut, RotateCcw } from "lucide-react";

interface ZoomControlsProps {
  zoomLevel: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onReset: () => void;
  className?: string;
}

export const ZoomControls: React.FC<ZoomControlsProps> = ({
  zoomLevel,
  onZoomIn,
  onZoomOut,
  onReset,
  className = "",
}) => {
  const percent = Math.round(zoomLevel * 100);

  return (
    <div
      className={`absolute bottom-4 right-4 flex items-center space-x-1 bg-[#161f33]/90 backdrop-blur-md border border-[#1f293d] rounded-xl px-2 py-1.5 shadow-xl text-slate-300 text-xs z-10 select-none ${className}`}
    >
      <button
        onClick={onZoomOut}
        title="Zoom Out (or scroll down)"
        className="p-1 hover:bg-[#1f293d] hover:text-white rounded-lg transition-colors"
      >
        <ZoomOut className="w-3.5 h-3.5" />
      </button>

      <span className="w-12 text-center font-mono text-[11px] font-semibold text-slate-400">
        {percent}%
      </span>

      <button
        onClick={onZoomIn}
        title="Zoom In (or scroll up)"
        className="p-1 hover:bg-[#1f293d] hover:text-white rounded-lg transition-colors"
      >
        <ZoomIn className="w-3.5 h-3.5" />
      </button>

      <div className="h-3 w-[1px] bg-[#1f293d] mx-1" />

      <button
        onClick={onReset}
        title="Reset Zoom & Pan"
        className="p-1 hover:bg-[#1f293d] hover:text-white rounded-lg transition-colors"
      >
        <RotateCcw className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};
