import React from "react";
import { RadarItem } from "../types";

interface ItemDetailModalProps {
  item: RadarItem | null;
  onClose: () => void;
}

export const ItemDetailModal: React.FC<ItemDetailModalProps> = ({ item, onClose }) => {
  if (!item) return null;

  const trajColor =
    item.lifecycle_stage === "Emerging"
      ? "text-sky-400 bg-sky-950/30 border-sky-500/30"
      : item.lifecycle_stage === "Consolidated"
      ? "text-emerald-400 bg-emerald-950/30 border-emerald-500/30"
      : "text-rose-400 bg-rose-950/30 border-rose-500/30";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-[#121826] border border-[#1f293d] rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex justify-between items-start p-6 border-b border-[#1f293d]">
          <div>
            <div className="flex items-center space-x-2">
              <span
                className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider border ${
                  item.track === "evaluation"
                    ? "bg-purple-950/50 text-purple-300 border-purple-500/40"
                    : "bg-blue-950/50 text-blue-300 border-blue-500/40"
                }`}
              >
                {item.track === "evaluation"
                  ? "Track: AI Evaluation"
                  : "Track: Software Testing"}
              </span>
              <span className="text-xs uppercase font-bold tracking-widest text-slate-400">
                • {item.category}
              </span>
            </div>
            <h2 className="text-2xl font-bold text-slate-100 mt-1">{item.name}</h2>
            <div className="flex items-center space-x-3 mt-2 flex-wrap gap-y-1">
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30">
                Ring: {item.recommended_ring}
              </span>
              <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-md border ${trajColor}`}>
                Trajectory: {item.lifecycle_stage}
              </span>
              {item.topic_name && (
                <span className="px-2.5 py-0.5 text-xs font-medium rounded-md bg-purple-900/30 text-purple-300 border border-purple-500/30">
                  Theme: {item.topic_name}
                </span>
              )}
              <span className="text-xs text-slate-400">{item.evidence_tier}</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 text-xl font-bold p-1"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
          {/* Scores Overview */}
          <div className="grid grid-cols-4 gap-3">
            <div className="bg-[#0b0f19] border border-[#1f293d] p-3 rounded-xl text-center">
              <div className="text-[11px] text-slate-400 uppercase font-semibold">Viability</div>
              <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
                {(item.viability_score * 100).toFixed(0)}%
              </div>
            </div>
            <div className="bg-[#0b0f19] border border-[#1f293d] p-3 rounded-xl text-center">
              <div className="text-[11px] text-slate-400 uppercase font-semibold">Hype Index</div>
              <div className="text-xl font-bold font-mono text-amber-400 mt-1">
                {(item.hype_score * 100).toFixed(0)}%
              </div>
            </div>
            <div className="bg-[#0b0f19] border border-[#1f293d] p-3 rounded-xl text-center">
              <div className="text-[11px] text-slate-400 uppercase font-semibold">Validity</div>
              <div className="text-xl font-bold font-mono text-blue-400 mt-1">
                {(item.validity_score * 100).toFixed(0)}%
              </div>
            </div>
            <div className="bg-[#0b0f19] border border-[#1f293d] p-3 rounded-xl text-center">
              <div className="text-[11px] text-slate-400 uppercase font-semibold">Corroboration</div>
              <div className="text-xl font-bold font-mono text-sky-400 mt-1">
                {item.corroboration_count}x
              </div>
            </div>
          </div>

          {/* Key Innovation */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Key Technical Innovation
            </h3>
            <p className="text-sm text-slate-200 leading-relaxed bg-[#0b0f19] p-4 rounded-xl border border-[#1f293d]">
              {item.key_innovation}
            </p>
          </div>

          {/* Independent Corroborating Sources */}
          {item.corroborating_sources && item.corroborating_sources.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-sky-400 mb-2">
                Multi-Source Topic Convergence ({item.corroborating_sources.length} sources)
              </h3>
              <ul className="space-y-1.5 bg-[#0b0f19] p-3 rounded-xl border border-[#1f293d]">
                {item.corroborating_sources.map((url, i) => (
                  <li key={i} className="text-xs truncate">
                    <a
                      href={url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-400 hover:text-blue-300 underline"
                    >
                      {url}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Operational Risks & Governance */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-red-400 mb-2">
              Adversarial Risks & Governance Constraints
            </h3>
            <ul className="space-y-2">
              {item.enterprise_risks.map((risk, i) => (
                <li
                  key={i}
                  className="text-xs text-red-300 bg-red-950/20 border border-red-900/30 px-3 py-2 rounded-lg flex items-start space-x-2"
                >
                  <span className="font-bold">•</span>
                  <span>{risk}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Prerequisites */}
          {item.prerequisites && item.prerequisites.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Operational Prerequisites
              </h3>
              <div className="flex flex-wrap gap-2">
                {item.prerequisites.map((prereq, i) => (
                  <span
                    key={i}
                    className="text-xs bg-[#161f33] text-slate-300 px-3 py-1 rounded-md border border-[#1f293d]"
                  >
                    {prereq}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Source Link */}
          <div>
            <a
              href={item.source_url}
              target="_blank"
              rel="noreferrer"
              className="inline-block text-xs font-semibold text-blue-400 hover:text-blue-300 underline"
            >
              Inspect Primary Source Payload ↗
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
