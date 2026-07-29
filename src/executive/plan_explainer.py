"""
MEMORA Executive Plan Explainer.

Generates caregiver-readable plan narratives explaining:
- Why the goal exists
- Why each task exists
- Ordering rationale
- Evidence supporting the plan
"""

from __future__ import annotations

from src.executive.executive_models import Goal, Plan


class PlanExplainer:
    """
    Generates human-readable explanations of generated executive plans.
    """

    @classmethod
    def generate_explanation(cls, goal: Goal, plan: Plan) -> str:
        """
        Produce a structured narrative explaining the plan.
        """
        lines = [
            f"### Executive Plan Explanation for Goal: '{goal.title}'",
            f"- **Goal Type**: {goal.goal_type.value}",
            f"- **Priority Score**: {goal.priority:.2f}",
            f"- **Confidence**: {plan.confidence:.0%}",
            f"- **Rationale**: {plan.rationale}",
            "",
            "**Task Sequence & Rationale**:",
        ]

        for idx, task in enumerate(plan.tasks, 1):
            lines.append(
                f"{idx}. **{task.title}** ({task.task_type.value}) - Est. {task.estimated_duration_sec:.0f}s"
            )
            if task.action_payload:
                lines.append(f"   - *Payload*: {task.action_payload}")

        lines.append("")
        lines.append(
            f"**Validation Status**: {'✅ VALIDATED' if plan.is_validated else '⚠️ UNVALIDATED'}"
        )
        return "\n".join(lines)
