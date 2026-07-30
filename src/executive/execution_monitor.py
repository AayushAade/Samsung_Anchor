"""
MEMORA Execution Monitor & Divergence Detector.

Tracks active plan execution progress and detects divergence between expected
and observed state (e.g. room change, object movement, execution timeout).
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from src.executive.executive_models import Plan, TaskNode, TaskStatus


class ExecutionMonitor:
    """
    Monitors execution progress and detects reality divergence.
    """

    def __init__(self) -> None:
        self.active_plan: Optional[Plan] = None
        self.task_start_times: Dict[str, float] = {}

    def set_active_plan(self, plan: Plan) -> None:
        self.active_plan = plan
        self.task_start_times.clear()

    def update_task_status(self, task_id: str, new_status: TaskStatus) -> None:
        if not self.active_plan:
            return
        for task in self.active_plan.tasks:
            if task.task_id == task_id:
                task.status = new_status
                if new_status == TaskStatus.EXECUTING:
                    self.task_start_times[task_id] = time.time()

    def check_divergence(
        self,
        current_location: str = "Living Room",
        observed_events: Optional[List[str]] = None,
    ) -> Tuple[bool, str]:
        """
        Check if observed reality diverges from the active plan's expectations.
        Returns (has_divergence, reason).
        """
        if not self.active_plan:
            return False, "No active plan"

        executing_tasks = [t for t in self.active_plan.tasks if t.status == TaskStatus.EXECUTING]

        for task in executing_tasks:
            target_room = task.action_payload.get("target_room")
            if target_room and target_room != current_location:
                return True, f"Room transition detected: User moved to {current_location} while task expected {target_room}."

            # Timeout check
            start_ts = self.task_start_times.get(task.task_id)
            if start_ts and (time.time() - start_ts) > (task.estimated_duration_sec * 3.0):
                return True, f"Execution timeout: Task '{task.title}' exceeded duration limit."

        return False, "Execution on track"

    def get_progress_summary(self) -> Dict[str, Any]:
        if not self.active_plan:
            return {"status": "NO_ACTIVE_PLAN", "completed_percent": 0.0}

        total = len(self.active_plan.tasks)
        if total == 0:
            return {"status": "EMPTY_PLAN", "completed_percent": 100.0}

        completed = sum(1 for t in self.active_plan.tasks if t.status == TaskStatus.COMPLETED)
        return {
            "plan_id": self.active_plan.plan_id,
            "total_tasks": total,
            "completed_tasks": completed,
            "completed_percent": round((completed / total) * 100.0, 1),
            "executing_tasks": [t.title for t in self.active_plan.tasks if t.status == TaskStatus.EXECUTING],
        }
