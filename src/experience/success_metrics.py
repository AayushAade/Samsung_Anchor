"""
MEMORA Success Metrics Engine.

Derives reproducible, deterministic performance metrics from accumulated execution records:
- Plan success rate
- Task completion rate
- Recovery effectiveness rate
- Interruption frequency
- Average execution latency
- Caregiver intervention rate
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.experience.experience_models import ExecutionOutcome, ExecutionRecord
from src.experience.experience_repository import ExperienceRepository


class SuccessMetricsEngine:
    """
    Computes deterministic operational metrics over execution histories.
    """

    @classmethod
    def compute_metrics(cls, repository: ExperienceRepository) -> Dict[str, Any]:
        """
        Compute reproducible success metrics across all stored execution records.
        """
        records = repository.get_all_records()
        total = len(records)

        if total == 0:
            return {
                "total_executions": 0,
                "plan_success_rate": 0.0,
                "task_completion_rate": 0.0,
                "recovery_effectiveness": 0.0,
                "interrupt_frequency": 0.0,
                "average_latency_ms": 0.0,
                "caregiver_intervention_rate": 0.0,
            }

        successful = sum(
            1 for r in records if r.completion_status in (ExecutionOutcome.SUCCESSFUL, ExecutionOutcome.RECOVERED)
        )
        recovered = sum(1 for r in records if r.completion_status == ExecutionOutcome.RECOVERED)
        total_recoveries_attempted = sum(len(r.recovery_actions) for r in records)
        interrupted = sum(1 for r in records if r.completion_status == ExecutionOutcome.INTERRUPTED or len(r.interruptions) > 0)
        caregiver_involved = sum(1 for r in records if r.caregiver_involvement)
        avg_latency = sum(r.latency_ms for r in records) / total

        total_tasks = sum(len(r.tasks_executed) for r in records)
        completed_tasks = sum(
            sum(1 for t in r.tasks_executed if t.get("status") == "COMPLETED") for r in records
        )
        task_completion_rate = (completed_tasks / max(1, total_tasks)) * 100.0

        recovery_effectiveness = (
            (recovered / max(1, total_recoveries_attempted)) * 100.0 if total_recoveries_attempted > 0 else 100.0
        )

        return {
            "total_executions": total,
            "successful_executions": successful,
            "plan_success_rate": round((successful / total) * 100.0, 1),
            "task_completion_rate": round(task_completion_rate, 1),
            "recovery_effectiveness": round(recovery_effectiveness, 1),
            "interrupt_frequency": round((interrupted / total) * 100.0, 1),
            "average_latency_ms": round(avg_latency, 2),
            "caregiver_intervention_rate": round((caregiver_involved / total) * 100.0, 1),
        }
