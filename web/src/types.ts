export type RadarRing = "Adopt" | "Trial" | "Assess" | "Hold";

export type QECategory =
  | "Spec & Model"
  | "Test Synthesis"
  | "Execution & Optimization"
  | "Triage & Self-Healing"
  | "Agent Systems"
  | "Governance & Evals";

export type EvidenceTier =
  | "Academic Peer-Reviewed"
  | "Open Source Repo"
  | "Engineering Post-Mortem"
  | "Vendor Announcement";

export type LifecycleStage = "Emerging" | "Consolidated" | "Fading";

export type TrackType = "testing" | "evaluation";

export interface RadarItem {
  id: string;
  name: string;
  track?: TrackType;
  category: QECategory;
  evidence_tier: EvidenceTier;
  hype_score: number;
  viability_score: number;
  validity_score: number;
  recommended_ring: RadarRing;
  lifecycle_stage: LifecycleStage;
  corroboration_count: number;
  velocity_score: number;
  corroborating_sources: string[];
  key_innovation: string;
  enterprise_risks: string[];
  prerequisites: string[];
  source_url: string;
  cluster_x?: number;
  cluster_y?: number;
}

export interface RadarData {
  radar_title: string;
  generated_at: string;
  rings: RadarRing[];
  categories: QECategory[];
  items: RadarItem[];
}
