"""
MEMORA Caregiver Intelligence & Clinical Oversight Explainer.

Generates deterministic Markdown reports synthesizing timeline overviews, trend analyses,
routine adherence metrics, assistance statistics, and escalation rule rationales.
"""

from __future__ import annotations

from typing import List

from src.caregiver.caregiver_engine import CaregiverEngine


class CaregiverExplainer:
    """
    Deterministic Markdown narrative generator for caregiver oversight reports.
    Synthesizes clinical observations into structured markdown reports without generative AI models,
    sentiment analysis, or speculative forecasting.
    """

    @classmethod
    def explain_engine_state(cls, engine: CaregiverEngine) -> str:
        """
        Generate a comprehensive, deterministic Markdown diagnostic report of current caregiver
        oversight state, timeline events, longitudinal trends, and clinical recommendations.
        """
        snap = engine.snapshot()
        summary = engine.generate_summary()
        highest, rules = engine.evaluate_escalation()
        trend_conf = engine.analyze_trends(metric="CONFUSION", window="7_DAYS")
        trend_rout = engine.analyze_trends(metric="ROUTINE", window="7_DAYS")
        trend_obj = engine.analyze_trends(metric="OBJECT", window="7_DAYS")
        timeline_events = engine.build_timeline()

        lines = [
            "# MEMORA Caregiver Intelligence & Clinical Oversight Diagnostic Report",
            "",
            "## Executive Summary",
            f"- **Patient Identifier**: `{summary.patient_id}`",
            f"- **Total Timeline Events**: {snap.total_events_count}",
            f"- **Summaries Generated**: {snap.summaries_generated_count}",
            f"- **Highest Escalation Level**: `{snap.highest_escalation.value}`",
            f"- **Oversight Checksum (SHA256)**: `{snap.checksum}`",
            "",
            "## Clinical Escalation Rating & Policy Rules",
            f"- **Current Escalation Rating**: `{highest.value}`",
            "### Supporting Policy Rules Evaluated",
        ]

        for r in rules:
            lines.append(f"- • {r}")

        lines.append("")
        lines.append("## Longitudinal Trend Analysis")
        lines.append(
            f"- **Confusion Trend**: `{trend_conf.trend_direction}` "
            f"({trend_conf.supporting_evidence[0] if trend_conf.supporting_evidence else 'N/A'})"
        )
        lines.append(
            f"- **Routine Adherence Trend**: `{trend_rout.trend_direction}` "
            f"({trend_rout.supporting_evidence[0] if trend_rout.supporting_evidence else 'N/A'})"
        )
        lines.append(
            f"- **Object Misplacement Search Trend**: `{trend_obj.trend_direction}` "
            f"({trend_obj.supporting_evidence[0] if trend_obj.supporting_evidence else 'N/A'})"
        )

        lines.append("")
        lines.append("## Timeline Overview")
        if timeline_events:
            for evt in timeline_events[:10]:
                ses_str = f" [Session: `{evt.session_id}`]" if evt.session_id else ""
                lines.append(
                    f"- **`{evt.event_type.value}`** ({evt.timestamp}): {evt.description}{ses_str}"
                )
        else:
            lines.append("• No events recorded in timeline.")

        lines.append("")
        lines.append("## Clinical Recommendations")
        all_recs = trend_conf.recommendations + trend_rout.recommendations + trend_obj.recommendations
        for rec in all_recs:
            lines.append(f"• {rec}")

        lines.append("")
        lines.append("## Evidence Sources & Clinical Boundary Audit")
        lines.append("• All trend analysis calculations derive from verified memory and timeline events.")
        lines.append("• Zero predictive forecasting, sentiment analysis, or machine learning models applied.")

        return "\n".join(lines)
