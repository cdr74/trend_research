"""Executive Markdown Intelligence Digest Generator."""

from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from radar.core.models import (
    EnterpriseEvaluation,
    RadarItem,
    TrendTopic,
)
from radar.db.tables import (
    EnterpriseEvaluationTable,
    RadarItemTable,
    TrendTopicTable,
)


class MarkdownReportGenerator:
    """Generates structured Markdown executive intelligence digests from radar entities."""

    @staticmethod
    def _get_attr(obj: Any, attr: str, default: Any = "") -> Any:
        """Safely retrieve attribute from Pydantic model or SQLAlchemy table."""
        if hasattr(obj, attr):
            val = getattr(obj, attr)
            if hasattr(val, "value"):
                return val.value
            return val
        return default

    def generate_markdown(
        self,
        items: Sequence[RadarItem | RadarItemTable],
        topics: Sequence[TrendTopic | TrendTopicTable] | None = None,
        evaluations: Sequence[EnterpriseEvaluation | EnterpriseEvaluationTable] | None = None,
        title: str = "Technology Horizon Radar - Executive Intelligence Digest",
    ) -> str:
        """Generate formatted Markdown report text."""
        now_str = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

        if not items:
            return (
                f"# {title}\n\n"
                f"*Generated on: {now_str}*\n\n"
                "> [!NOTE]\n"
                "> No evaluated radar items available in the current corpus.\n"
            )

        ring_counts = Counter(self._get_attr(item, "recommended_ring") for item in items)
        adopt_count = ring_counts.get("Adopt", 0)
        trial_count = ring_counts.get("Trial", 0)
        assess_count = ring_counts.get("Assess", 0)
        hold_count = ring_counts.get("Hold", 0)

        lines: list[str] = [
            f"# {title}",
            "",
            f"*Generated on: {now_str} | Evaluated Items: {len(items)} | Converged Topics: {len(topics or [])}*",
            "",
            "## 1. Executive Summary & Ring Distribution",
            "",
            f"The Trend Horizon Radar currently tracks **{len(items)} evaluated technologies** across 6 Quality Engineering pillars. "
            f"Recommendations break down as follows: **{adopt_count} Adopt**, **{trial_count} Trial**, **{assess_count} Assess**, and **{hold_count} Hold**.",
            "",
            "| Ring | Technology | QE Pillar | Viability | Hype | Trajectory | Key Innovation |",
            "| :--- | :--- | :--- | :---: | :---: | :---: | :--- |",
        ]

        # Sort items: Adopt -> Trial -> Assess -> Hold, then descending viability
        ring_order = {"Adopt": 0, "Trial": 1, "Assess": 2, "Hold": 3}
        sorted_items = sorted(
            items,
            key=lambda x: (
                ring_order.get(str(self._get_attr(x, "recommended_ring")), 99),
                -float(self._get_attr(x, "viability_score", 0.0)),
            ),
        )

        for it in sorted_items:
            ring = str(self._get_attr(it, "recommended_ring"))
            name = str(self._get_attr(it, "name"))
            category = str(self._get_attr(it, "category"))
            viab = float(self._get_attr(it, "viability_score", 0.0))
            hype = float(self._get_attr(it, "hype_score", 0.0))
            traj = str(self._get_attr(it, "lifecycle_stage"))
            innov = str(self._get_attr(it, "key_innovation"))
            if len(innov) > 60:
                innov = innov[:57] + "..."

            lines.append(
                f"| **{ring.upper()}** | `{name}` | {category} | {viab:.2f} | {hype:.2f} | *{traj}* | {innov} |"
            )

        # 2. Converged Technology Topics
        if topics:
            lines.extend(
                [
                    "",
                    "## 2. Converged Technology Trends (Cross-Source Corroboration)",
                    "",
                    "Independent topic clusters showing semantic consensus across academic, open source, and practitioner channels:",
                    "",
                    "| Topic Name | QE Pillar | Corroborations | Validity | Synthesis Summary |",
                    "| :--- | :--- | :---: | :---: | :--- |",
                ]
            )
            for t in topics:
                t_name = str(self._get_attr(t, "name"))
                t_cat = str(self._get_attr(t, "category"))
                t_count = int(self._get_attr(t, "corroboration_count", 1))
                t_val = float(self._get_attr(t, "average_validity", 0.0))
                t_summary = str(self._get_attr(t, "summary"))
                lines.append(f"| **{t_name}** | {t_cat} | {t_count} | {t_val:.2f} | {t_summary} |")

        # 3. High-Priority Recommendations (Adopt & Trial)
        top_candidates = [
            x
            for x in sorted_items
            if str(self._get_attr(x, "recommended_ring")) in ("Adopt", "Trial")
        ]
        if top_candidates:
            lines.extend(
                [
                    "",
                    "## 3. High-Priority Technology Spotlights (Adopt & Trial)",
                    "",
                ]
            )
            for c in top_candidates:
                c_name = str(self._get_attr(c, "name"))
                c_ring = str(self._get_attr(c, "recommended_ring")).upper()
                c_cat = str(self._get_attr(c, "category"))
                c_tier = str(self._get_attr(c, "evidence_tier"))
                c_innov = str(self._get_attr(c, "key_innovation"))
                c_url = str(self._get_attr(c, "source_url"))
                c_prereqs = list(self._get_attr(c, "prerequisites", []))

                lines.append(f"### `{c_name}` — [{c_ring}]")
                lines.append(f"- **Pillar:** {c_cat} | **Evidence Tier:** {c_tier}")
                lines.append(f"- **Source Reference:** [{c_url}]({c_url})")
                lines.append(f"- **Innovation Summary:** {c_innov}")
                if c_prereqs:
                    lines.append(
                        f"- **Adoption Prerequisites:** {', '.join(str(p) for p in c_prereqs)}"
                    )
                lines.append("")

        # 4. Adversarial Skeptic & Risk Radar
        all_risks: set[str] = set()
        for it in items:
            for r in self._get_attr(it, "enterprise_risks", []):
                all_risks.add(str(r))
        if evaluations:
            for ev in evaluations:
                for r in self._get_attr(ev, "enterprise_risks", []):
                    all_risks.add(str(r))

        if all_risks:
            lines.extend(
                [
                    "## 4. Adversarial Committee Risk Radar",
                    "",
                    "> [!WARNING]",
                    "> The following architectural and security risks were identified by the multi-lens committee:",
                    "",
                ]
            )
            for risk in sorted(all_risks):
                lines.append(f"- ⚠️ **Risk:** {risk}")
            lines.append("")

        # 5. Parasitic Wrapper & Marketing Quarantine Log
        hold_items = [
            x for x in sorted_items if str(self._get_attr(x, "recommended_ring")) == "Hold"
        ]
        if hold_items:
            lines.extend(
                [
                    "## 5. Wrapper Quarantine & Anti-Hype Log",
                    "",
                    "Technologies relegated to **HOLD** due to high marketing hype (> 0.60), superficial wrapper architecture, or lack of empirical artifacts:",
                    "",
                ]
            )
            for h in hold_items:
                h_name = str(self._get_attr(h, "name"))
                h_hype = float(self._get_attr(h, "hype_score", 0.0))
                h_innov = str(self._get_attr(h, "key_innovation"))
                lines.append(f"- 🛑 **`{h_name}`** (Hype: {h_hype:.2f}): {h_innov}")
            lines.append("")

        # 6. Audience Velocity Movers
        emerging = [
            x
            for x in sorted_items
            if str(self._get_attr(x, "lifecycle_stage")) == "Emerging"
            and float(self._get_attr(x, "velocity_score", 0.0)) >= 20.0
        ]
        fading = [x for x in sorted_items if str(self._get_attr(x, "lifecycle_stage")) == "Fading"]
        if emerging or fading:
            lines.extend(
                [
                    "## 6. Audience Velocity Movers",
                    "",
                ]
            )
            if emerging:
                lines.append("### 🚀 Fast-Moving Emerging Trends")
                for e in emerging:
                    lines.append(
                        f"- **`{self._get_attr(e, 'name')}`** (Velocity: {float(self._get_attr(e, 'velocity_score')):.1f}): {self._get_attr(e, 'key_innovation')}"
                    )
                lines.append("")
            if fading:
                lines.append("### 📉 Stagnant or Fading Tools")
                for f in fading:
                    lines.append(
                        f"- **`{self._get_attr(f, 'name')}`** (Velocity: {float(self._get_attr(f, 'velocity_score')):.1f})"
                    )
                lines.append("")

        return "\n".join(lines)

    def generate_and_save(
        self,
        items: Sequence[RadarItem | RadarItemTable],
        output_path: str | Path,
        topics: Sequence[TrendTopic | TrendTopicTable] | None = None,
        evaluations: Sequence[EnterpriseEvaluation | EnterpriseEvaluationTable] | None = None,
        title: str = "Technology Horizon Radar - Executive Intelligence Digest",
    ) -> Path:
        """Generate markdown report and write to destination file."""
        report_text = self.generate_markdown(
            items=items,
            topics=topics,
            evaluations=evaluations,
            title=title,
        )
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report_text, encoding="utf-8")
        return path
