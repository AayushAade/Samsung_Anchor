"""
MEMORA Recovery Manager.

Provides structured, explainable recovery strategies for plan execution failures:
- RETRY: Retry transient task failure
- FALLBACK: Fall back to alternative spatial location or secondary strategy
- WAIT: Pause and wait for sensor/confidence recovery
- REQUEST_EVIDENCE: Prompt user or query additional sensory evidence
- ESCALATE: Escalate to caregiver or safety framework
- TERMINATE: Gracefully terminate plan
"""

from __future__ import annotations

from typing import Optional

from src.executive.executive_models import RecoveryAction, RecoveryStrategy, TaskNode, TaskType


class RecoveryManager:
    """
    Evaluates execution failures and selects structured recovery actions.
    """

    @classmethod
    def evaluate_recovery(
        cls,
        failed_task: TaskNode,
        failure_reason: str,
        attempt_count: int = 1,
    ) -> RecoveryAction:
        """
        Determine appropriate recovery strategy for a task failure.
        """
        f_lower = failure_reason.lower()

        if "timeout" in f_lower and attempt_count <= 2:
            return RecoveryAction(
                strategy=RecoveryStrategy.RETRY,
                target_task_id=failed_task.task_id,
                explanation=f"Transient timeout on '{failed_task.title}'. Attempting retry ({attempt_count}/2).",
            )

        if failed_task.task_type == TaskType.SEARCH_ROOM:
            return RecoveryAction(
                strategy=RecoveryStrategy.FALLBACK,
                target_task_id=failed_task.task_id,
                explanation=f"Item not found in primary room ({failed_task.action_payload.get('location')}). Falling back to secondary location (Bedside Table).",
            )

        if "sensor" in f_lower or "confidence" in f_lower:
            return RecoveryAction(
                strategy=RecoveryStrategy.WAIT,
                target_task_id=failed_task.task_id,
                explanation="Sensor confidence degraded. Pausing task and waiting for signal recovery.",
            )

        if "emergency" in f_lower or "safety" in f_lower:
            return RecoveryAction(
                strategy=RecoveryStrategy.ESCALATE,
                target_task_id=failed_task.task_id,
                explanation="Safety alert detected during task execution. Escalating to Caregiver Framework.",
            )

        return RecoveryAction(
            strategy=RecoveryStrategy.TERMINATE,
            target_task_id=failed_task.task_id,
            explanation=f"Unrecoverable failure on task '{failed_task.title}'. Gracefully terminating active plan.",
        )
