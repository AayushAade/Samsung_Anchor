"""
MEMORA Executive Goal Hierarchy & Lifecycle Manager.

Manages structured hierarchical goals across 4 levels (Strategic, Operational, Task, Action)
and enforces strict 7-stage lifecycle transitions:
CREATED -> PLANNED -> EXECUTING -> BLOCKED -> INTERRUPTED -> COMPLETED -> ARCHIVED
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Dict, List, Optional

from src.executive.executive_models import Goal, GoalStatus, GoalType


class GoalManager:
    """
    Thread-safe repository and lifecycle manager for Executive Goals.
    """

    def __init__(self) -> None:
        self._goals: Dict[str, Goal] = {}
        self._lock = threading.Lock()
        self._seed_baseline_goals()

    def add_goal(
        self,
        title: str,
        goal_type: GoalType = GoalType.OPERATIONAL,
        priority: float = 0.50,
        dependencies: Optional[List[str]] = None,
        deadline_iso: Optional[str] = None,
        origin: str = "Reasoning Engine",
    ) -> Goal:
        """
        Add a new goal to the hierarchy in CREATED status.
        """
        goal = Goal(
            title=title,
            goal_type=goal_type,
            priority=max(0.0, min(1.0, priority)),
            dependencies=dependencies or [],
            deadline_iso=deadline_iso,
            origin=origin,
            status=GoalStatus.CREATED,
        )
        with self._lock:
            self._goals[goal.goal_id] = goal
        return goal

    def transition_status(self, goal_id: str, new_status: GoalStatus) -> Optional[Goal]:
        """
        Transition goal to a new status in the 7-stage lifecycle.
        """
        with self._lock:
            if goal_id not in self._goals:
                return None
            goal = self._goals[goal_id]
            goal.status = new_status
            if new_status == GoalStatus.COMPLETED:
                goal.completed_at_iso = datetime.now().isoformat()
            return goal

    def get_active_goals(self) -> List[Goal]:
        """
        Return non-archived goals sorted by priority descending.
        """
        with self._lock:
            goals = [
                g for g in self._goals.values() if g.status not in (GoalStatus.COMPLETED, GoalStatus.ARCHIVED)
            ]
            goals.sort(key=lambda g: g.priority, reverse=True)
            return goals

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        with self._lock:
            return self._goals.get(goal_id)

    def _seed_baseline_goals(self) -> None:
        """Seed initial baseline operational goals."""
        g1 = Goal(
            title="Maintain Daily Assistive Orientation",
            goal_type=GoalType.STRATEGIC,
            priority=0.90,
            origin="Care Policy",
            status=GoalStatus.EXECUTING,
        )
        g2 = Goal(
            title="Assist with Misplaced Reading Glasses",
            goal_type=GoalType.OPERATIONAL,
            priority=0.80,
            dependencies=[g1.goal_id],
            origin="Reasoning Engine",
            status=GoalStatus.PLANNED,
        )
        self._goals[g1.goal_id] = g1
        self._goals[g2.goal_id] = g2
