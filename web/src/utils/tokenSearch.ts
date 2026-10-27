import { RadarItem } from "../types";

export interface ParsedQuery {
  ring?: string;
  track?: string;
  category?: string;
  tier?: string;
  stage?: string;
  minViability?: number;
  maxViability?: number;
  minHype?: number;
  maxHype?: number;
  risk?: string;
  freeTerms: string[];
}

export function parseSearchQuery(query: string): ParsedQuery {
  const parsed: ParsedQuery = { freeTerms: [] };
  if (!query || query.trim() === "") {
    return parsed;
  }

  // Regex to match token:value or "quoted words" or single words
  const regex = /(\b[a-zA-Z_-]+:(?:>|<|>=|<=)?"[^"]+"|\b[a-zA-Z_-]+:(?:>|<|>=|<=)?[^\s]+|"[^"]+"|[^\s]+)/g;
  const matches = query.match(regex);
  if (!matches) return parsed;

  for (const rawToken of matches) {
    const token = rawToken.trim();
    if (!token) continue;

    if (token.includes(":")) {
      const colonIdx = token.indexOf(":");
      const key = token.slice(0, colonIdx).toLowerCase();
      let val = token.slice(colonIdx + 1);

      // Strip quotes if any
      if (val.startsWith('"') && val.endsWith('"')) {
        val = val.slice(1, -1);
      }

      if (key === "ring") {
        parsed.ring = val.toLowerCase();
      } else if (key === "track" || key === "type") {
        parsed.track = val.toLowerCase();
      } else if (key === "category" || key === "pillar") {
        parsed.category = val.toLowerCase();
      } else if (key === "tier" || key === "evidence") {
        parsed.tier = val.toLowerCase();
      } else if (key === "stage" || key === "lifecycle") {
        parsed.stage = val.toLowerCase();
      } else if (key === "risk") {
        parsed.risk = val.toLowerCase();
      } else if (key === "viability") {
        if (val.startsWith(">=") || val.startsWith(">")) {
          const num = parseFloat(val.replace(/[>=]/g, ""));
          if (!isNaN(num)) parsed.minViability = num;
        } else if (val.startsWith("<=") || val.startsWith("<")) {
          const num = parseFloat(val.replace(/[<=]/g, ""));
          if (!isNaN(num)) parsed.maxViability = num;
        } else {
          const num = parseFloat(val);
          if (!isNaN(num)) parsed.minViability = num;
        }
      } else if (key === "hype") {
        if (val.startsWith(">=") || val.startsWith(">")) {
          const num = parseFloat(val.replace(/[>=]/g, ""));
          if (!isNaN(num)) parsed.minHype = num;
        } else if (val.startsWith("<=") || val.startsWith("<")) {
          const num = parseFloat(val.replace(/[<=]/g, ""));
          if (!isNaN(num)) parsed.maxHype = num;
        } else {
          const num = parseFloat(val);
          if (!isNaN(num)) parsed.maxHype = num;
        }
      } else {
        parsed.freeTerms.push(val.toLowerCase());
      }
    } else {
      let term = token;
      if (term.startsWith('"') && term.endsWith('"')) {
        term = term.slice(1, -1);
      }
      parsed.freeTerms.push(term.toLowerCase());
    }
  }

  return parsed;
}

export function matchesQuery(item: RadarItem, parsed: ParsedQuery): boolean {
  if (parsed.ring && item.recommended_ring.toLowerCase() !== parsed.ring) {
    return false;
  }

  if (parsed.track && item.track && !item.track.toLowerCase().includes(parsed.track)) {
    return false;
  }

  if (parsed.category && !item.category.toLowerCase().includes(parsed.category)) {
    return false;
  }

  if (parsed.tier) {
    const tier = item.evidence_tier.toLowerCase();
    if (!tier.includes(parsed.tier) && !(parsed.tier === "oss" && tier.includes("open source"))) {
      return false;
    }
  }

  if (parsed.stage && !item.lifecycle_stage.toLowerCase().includes(parsed.stage)) {
    return false;
  }

  if (parsed.minViability !== undefined && item.viability_score < parsed.minViability) {
    return false;
  }

  if (parsed.maxViability !== undefined && item.viability_score > parsed.maxViability) {
    return false;
  }

  if (parsed.minHype !== undefined && item.hype_score < parsed.minHype) {
    return false;
  }

  if (parsed.maxHype !== undefined && item.hype_score > parsed.maxHype) {
    return false;
  }

  if (parsed.risk) {
    const hasRisk = item.enterprise_risks.some((r) =>
      r.toLowerCase().includes(parsed.risk!)
    );
    if (!hasRisk) return false;
  }

  if (parsed.freeTerms.length > 0) {
    const searchable = [
      item.name,
      item.key_innovation,
      item.category,
      item.evidence_tier,
      item.source_url,
      ...item.enterprise_risks,
      ...item.prerequisites,
    ]
      .join(" ")
      .toLowerCase();

    for (const term of parsed.freeTerms) {
      if (!searchable.includes(term)) {
        return false;
      }
    }
  }

  return true;
}
