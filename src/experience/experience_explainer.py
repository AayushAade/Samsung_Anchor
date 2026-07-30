"""
MEMORA Experience Explainer.

Generates caregiver-readable narratives explaining:
- Experience recommendations provided to Executive Planner
- Confidence calibration rationale
- Routine optimization choices
"""

from __future__ import annotations

from src.experience.experience_models import CalibratedConfidence, ExecutionPattern


class ExperienceExplainer:
    """
    Generates human-readable explanations of experience learning recommendations.
    """

    @classmethod
    def generate_recommendation_explanation(
        cls,
        pattern: ExecutionPattern,
        calibration: CalibratedConfidence,
    ) -> str:
        """
        Produce a structured narrative explaining experience recommendations.
        """
        lines = [
            f"### Experience Learning Recommendation for '{pattern.goal_title}'",
            f"- **Historical Executions**: {pattern.usage_count}",
            f"- **Success Rate**: {pattern.success_rate:.0%}",
            f"- **Average Latency**: {pattern.average_latency_ms:.1f}ms",
            f"- **Calibrated Confidence**: {calibration.recommended_confidence:.0%}",
            f"- **Calibration Explanation**: {calibration.calibration_explanation}",
            "",
            "**Recommended Task Sequence**:",
        ]

        for idx, task_title in enumerate(pattern.task_sequence_titles, 1):
            lines.append(f"{idx}. {task_title}")

        return "\n".join(lines)
