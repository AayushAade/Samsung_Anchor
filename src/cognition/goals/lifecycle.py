"""
Samsung Anchor — Goal Lifecycle Manager.

Handles temporal evolution: state transitions, confidence decay,
expiration of stale goals, and activation of confirmed goals.
"""

from __future__ import annotations

from src.cognition.goals.models import GoalHypothesis, GoalState


class GoalLifecycleManager:
    """
    Applies lifecycle rules to a GoalHypothesis in-place.
    Called by the GoalInferenceEngine after every cognitive cycle.
    """

    MAX_STALE_CYCLES = 2

    def evolve(self, goal: GoalHypothesis) -> None:
        """
        Apply one cycle of temporal evolution to a goal.
        """
        # 1. Apply temporal confidence decay
        goal.confidence = goal.confidence * goal.DECAY_FACTOR

        # 2. Check for state transitions
        if goal.state == GoalState.HYPOTHESIZED:
            if goal.confidence >= goal.ACTIVATION_THRESHOLD:
                goal.state = GoalState.ACTIVE
                goal.stale_cycles = 0

        elif goal.state == GoalState.ACTIVE:
            if goal.confidence < goal.ABANDONMENT_THRESHOLD:
                goal.stale_cycles += 1
                if goal.stale_cycles >= self.MAX_STALE_CYCLES:
                    goal.state = GoalState.ABANDONED
            else:
                goal.stale_cycles = 0

        elif goal.state == GoalState.INTERRUPTED:
            # Interrupted goals can reactivate if confidence rises
            if goal.confidence >= goal.ACTIVATION_THRESHOLD:
                goal.state = GoalState.ACTIVE
                goal.stale_cycles = 0

    def mark_completed(self, goal: GoalHypothesis) -> None:
        """Explicitly mark a goal as completed (e.g., via feedback)."""
        goal.state = GoalState.COMPLETED

    def interrupt(self, goal: GoalHypothesis) -> None:
        """Temporarily displace an active goal."""
        if goal.state == GoalState.ACTIVE:
            goal.state = GoalState.INTERRUPTED
