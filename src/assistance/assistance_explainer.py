"""
MEMORA Alzheimer's Cognitive Assistance Explainer.

Generates deterministic Markdown summaries of active assistance plans, scenario distributions,
caregiver reports, reassurance statistics, and escalation alerts for clinical team review.
"""

from __future__ import annotations

from typing import List

from src.assistance.assistance_engine import AssistanceEngine


class AssistanceExplainer:
    """
    Deterministic Markdown narrative generator for Alzheimer's cognitive assistance workflows.
    """

    @classmethod
    def explain_engine_state(cls, engine: AssistanceEngine) -> str:
        snap = engine.snapshot()
        cg_summary = engine.summarize_caregiver()
        plans = list(engine._active_plans.values())
        outcomes = engine._executed_outcomes

        lines = [
            "# MEMORA Alzheimer's Cognitive Assistance Diagnostic Report",
            "",
            "## Executive Summary",
            f"- **Active Assistance Plans Count**: {snap.active_plans_count}",
            f"- **Executed Outcomes Count**: {snap.executed_outcomes_count}",
            f"- **Escalations Flagged**: {snap.escalations_count}",
            f"- **Framework Checksum (SHA256)**: `{snap.checksum}`",
            "",
            "## Caregiver Summary",
            f"- **Patient**: `{cg_summary.get('patient_id')}`",
            f"- **Total Interventions**: {cg_summary.get('total_interventions')}",
            f"- **Escalation Count**: {cg_summary.get('escalation_count')}",
            f"- **Caregiver Note**: {cg_summary.get('summary')}",
            f"- **Recommended Next Action**: {cg_summary.get('recommended_action')}",
            "",
            "## Active Assistance Plans Breakdown",
        ]

        if plans:
            for p in plans:
                lines.append(
                    f"- **`{p.plan_id}`** (Session: `{p.session_id}`) — Scenario: `{p.scenario.value}` Priority: `{p.priority.value}`"
                )
        else:
            lines.append("• No active assistance plans pending.")

        lines.append("")
        lines.append("## Executed Outcome History")
        if outcomes:
            for plan, outcome in outcomes:
                esc_str = " [ESCALATION FLAGGED]" if outcome.escalation_required else ""
                lines.append(
                    f"- Plan `{plan.plan_id}` ({plan.scenario.value}) → {outcome.summary}{esc_str}"
                )
        else:
            lines.append("• No assistance outcomes executed yet.")

        lines.append("")
        lines.append("## Recommended Next Actions")
        if snap.escalations_count > 0:
            lines.append("• Review caregiver escalation notifications for frequent repetition loops or disorientation.")
        lines.append("• Maintain daily routine guidance step-by-step progress tracking.")

        return "\n".join(lines)
