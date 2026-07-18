"""
Samsung Anchor — Goal Repository.

In-memory store for active goal hypotheses with an archive
for recently expired goals (for observability / inspection).
"""

from __future__ import annotations

from typing import Dict, List

from src.cognition.goals.models import GoalHypothesis, GoalState


class GoalRepository:
    """
    Holds the current set of active goal hypotheses and an archive
    of completed / abandoned goals.
    """

    MAX_ACTIVE = 5
    MAX_ARCHIVE = 20

    def __init__(self) -> None:
        self._active: Dict[str, GoalHypothesis] = {}
        self._archive: List[GoalHypothesis] = []

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_active_goals(self) -> List[GoalHypothesis]:
        """Return all active (non-terminal) goals sorted by confidence desc."""
        goals = list(self._active.values())
        goals.sort(key=lambda g: g.confidence, reverse=True)
        return goals

    def get_by_name(self, name: str) -> GoalHypothesis | None:
        return self._active.get(name)

    def get_archive(self) -> List[GoalHypothesis]:
        return list(self._archive)

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def upsert(self, goal: GoalHypothesis) -> None:
        """Insert or update a goal hypothesis in the active set."""
        if goal.state in (GoalState.COMPLETED, GoalState.ABANDONED):
            # Terminal goals go to archive
            self._archive_goal(goal)
        else:
            self._active[goal.name] = goal
            self._enforce_capacity()

    def archive_terminal_goals(self) -> None:
        """Move any goals that reached a terminal state to the archive."""
        to_archive = [
            name
            for name, g in self._active.items()
            if g.state in (GoalState.COMPLETED, GoalState.ABANDONED)
        ]
        for name in to_archive:
            self._archive_goal(self._active.pop(name))

    def clear(self) -> None:
        self._active.clear()
        self._archive.clear()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _archive_goal(self, goal: GoalHypothesis) -> None:
        self._archive.append(goal)
        if len(self._archive) > self.MAX_ARCHIVE:
            self._archive = self._archive[-self.MAX_ARCHIVE :]

    def _enforce_capacity(self) -> None:
        """If we exceed MAX_ACTIVE, drop the lowest-confidence goal."""
        while len(self._active) > self.MAX_ACTIVE:
            weakest = min(self._active.values(), key=lambda g: g.confidence)
            weakest.state = GoalState.ABANDONED
            self._archive_goal(self._active.pop(weakest.name))
