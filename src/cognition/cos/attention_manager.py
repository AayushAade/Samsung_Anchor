"""
Cognitive Operating System — Attention Manager.

Wraps the existing CognitiveAttentionEngine's INTERRUPT/SILENCE decisions
with explicit focus lifecycle tracking (acquire → maintain → release → interrupt).

Does NOT replace the existing attention scorer pipeline.
"""

from __future__ import annotations

import time
from typing import Any

from src.cognition.attention.attention_models import AttentionDecision
from src.cognition.cos.models import AttentionFocus, AttentionFocusState
from src.cognition.goals.models import GoalHypothesis, GoalState


class AttentionManager:
    """
    Tracks the current cognitive focus target across reasoning cycles.

    Lifecycle:
        IDLE → ACQUIRED (when attention engine triggers INTERRUPT)
             → MAINTAINED (on subsequent cycles if same target persists)
             → INTERRUPTED (when a higher-priority target displaces current)
             → RELEASED (when attention engine returns SILENCE or goal completes)
    """

    def __init__(self) -> None:
        self._focus = AttentionFocus()

    def update_focus(
        self,
        attention_decision: AttentionDecision | None,
        goals: list[GoalHypothesis] | None = None,
    ) -> AttentionFocus:
        """
        Update attention focus based on the latest attention engine decision
        and active goal distribution.

        Parameters
        ----------
        attention_decision : AttentionDecision | None
            The INTERRUPT/SILENCE output from the existing CognitiveAttentionEngine.
        goals : list[GoalHypothesis] | None
            Current active goal hypotheses for priority derivation.

        Returns
        -------
        AttentionFocus
            The updated focus state.
        """
        # Derive new target from attention decision + top goal
        new_target = self._derive_target(attention_decision, goals)
        should_interrupt = attention_decision.should_interrupt if attention_decision else False

        if not should_interrupt:
            # Attention engine says SILENCE — release any held focus
            if self._focus.state in (AttentionFocusState.ACQUIRED, AttentionFocusState.MAINTAINED):
                self._focus.state = AttentionFocusState.RELEASED
            else:
                self._focus.state = AttentionFocusState.IDLE
            return self._focus

        # Attention engine says INTERRUPT
        if self._focus.state == AttentionFocusState.IDLE or self._focus.state == AttentionFocusState.RELEASED:
            # Fresh acquisition
            self._focus = AttentionFocus(
                target=new_target,
                state=AttentionFocusState.ACQUIRED,
                acquired_at=time.time(),
                cycle_count=1,
                priority_score=attention_decision.highest_score if attention_decision else 0.0,
            )
        elif new_target == self._focus.target:
            # Same target persists — maintain
            self._focus.state = AttentionFocusState.MAINTAINED
            self._focus.cycle_count += 1
            self._focus.priority_score = attention_decision.highest_score if attention_decision else self._focus.priority_score
        else:
            # Different target — interrupt current, acquire new
            self._focus = AttentionFocus(
                target=new_target,
                state=AttentionFocusState.ACQUIRED,
                acquired_at=time.time(),
                cycle_count=1,
                priority_score=attention_decision.highest_score if attention_decision else 0.0,
            )

        return self._focus

    def get_current_focus(self) -> AttentionFocus:
        """Return the current attention focus snapshot."""
        return self._focus

    def release_focus(self) -> None:
        """Explicitly release the current focus target."""
        self._focus.state = AttentionFocusState.RELEASED

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _derive_target(
        attention_decision: AttentionDecision | None,
        goals: list[GoalHypothesis] | None,
    ) -> str:
        """
        Derive a human-readable focus target label from attention + goals.
        """
        # Primary: top active goal
        if goals:
            active = [g for g in goals if g.state in (GoalState.HYPOTHESIZED, GoalState.ACTIVE)]
            if active:
                top = max(active, key=lambda g: g.confidence)
                return top.name

        # Fallback: top attended memory summary
        if attention_decision and attention_decision.selected_memories:
            top_mem = attention_decision.selected_memories[0]
            return f"Memory: {top_mem.summary[:60]}"

        return "General Observation"
