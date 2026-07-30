"""
Cognitive Operating System — Decision Engine.

Multi-factor action selector. Given context, goals, attention focus,
working memory, and patient state — selects the optimal CognitiveAction
with a documented reasoning path.

Does NOT replace CarePolicyFramework. Consults patient state and goals
to produce a higher-level cognitive recommendation that the pipeline
then feeds into the existing care policy evaluation.
"""

from __future__ import annotations

from typing import Any

from src.cognition.context.models import CognitiveContext
from src.cognition.cos.models import (
    AttentionFocus,
    AttentionFocusState,
    CognitiveAction,
    CognitiveActionType,
)
from src.cognition.goals.models import GoalHypothesis, GoalCategory, GoalState
from src.clinical.patient_state import PatientState, PatientStateMode


class DecisionEngine:
    """
    Selects the next cognitive action by evaluating multi-domain inputs.

    Decision priority (highest to lowest):
        1. Emergency / Safety override
        2. Active goal with high confidence
        3. Attention-driven memory retrieval
        4. Conversational follow-up from working memory
        5. Supportive silence (default)
    """

    def decide(
        self,
        context: CognitiveContext | None,
        goals: list[GoalHypothesis] | None,
        focus: AttentionFocus,
        working_memory_snapshot: dict[str, Any],
        patient_state: PatientState | None,
    ) -> CognitiveAction:
        """
        Evaluate all cognitive inputs and return a CognitiveAction.

        Returns
        -------
        CognitiveAction
            The recommended action with reasoning path documentation.
        """
        reasoning_steps: list[str] = []

        # ---------------------------------------------------------------
        # Priority 1: Emergency / Safety override
        # ---------------------------------------------------------------
        if patient_state and patient_state.mode == PatientStateMode.EMERGENCY:
            reasoning_steps.append("P1: Emergency state detected → ESCALATE_TO_CAREGIVER")
            return CognitiveAction(
                action_type=CognitiveActionType.ESCALATE_TO_CAREGIVER,
                reasoning_path=" → ".join(reasoning_steps),
                confidence=1.0,
                suggested_message="Emergency safety trigger active. Caregiver notified.",
            )

        # ---------------------------------------------------------------
        # Priority 2: High-confidence active goal
        # ---------------------------------------------------------------
        top_goal = self._get_top_active_goal(goals)
        if top_goal and top_goal.confidence >= 0.40:
            action = self._action_for_goal(top_goal, patient_state)
            reasoning_steps.append(
                f"P2: Active goal '{top_goal.name}' (conf={top_goal.confidence:.2f}) → {action.action_type.value}"
            )
            action.reasoning_path = " → ".join(reasoning_steps)
            return action

        # ---------------------------------------------------------------
        # Priority 3: Attention-driven response
        # ---------------------------------------------------------------
        if focus.state in (AttentionFocusState.ACQUIRED, AttentionFocusState.MAINTAINED):
            reasoning_steps.append(
                f"P3: Attention focus '{focus.target}' ({focus.state.value}) → SPEAK"
            )
            return CognitiveAction(
                action_type=CognitiveActionType.SPEAK,
                reasoning_path=" → ".join(reasoning_steps),
                confidence=0.80,
                metadata={"attention_target": focus.target},
            )

        # ---------------------------------------------------------------
        # Priority 4: Working memory conversational follow-up
        # ---------------------------------------------------------------
        wm_slots = working_memory_snapshot.get("slots", {})
        if "current_conversation" in wm_slots:
            slot_data = wm_slots["current_conversation"]
            if not slot_data.get("is_expired", True):
                reasoning_steps.append("P4: Active conversation in working memory → SPEAK")
                return CognitiveAction(
                    action_type=CognitiveActionType.SPEAK,
                    reasoning_path=" → ".join(reasoning_steps),
                    confidence=0.70,
                    metadata={"working_memory_key": "current_conversation"},
                )

        # ---------------------------------------------------------------
        # Priority 5: Patient needs gentle support
        # ---------------------------------------------------------------
        if patient_state and patient_state.mode in (
            PatientStateMode.ANXIOUS,
            PatientStateMode.DISORIENTED,
            PatientStateMode.REPETITIVE,
        ):
            reasoning_steps.append(
                f"P5: Patient state '{patient_state.mode.value}' → SPEAK (care policy)"
            )
            return CognitiveAction(
                action_type=CognitiveActionType.SPEAK,
                reasoning_path=" → ".join(reasoning_steps),
                confidence=0.85,
                metadata={"patient_mode": patient_state.mode.value},
            )

        # ---------------------------------------------------------------
        # Default: Supportive silence
        # ---------------------------------------------------------------
        reasoning_steps.append("DEFAULT: No active goal, no attention, no urgent state → REMAIN_SILENT")
        return CognitiveAction(
            action_type=CognitiveActionType.REMAIN_SILENT,
            reasoning_path=" → ".join(reasoning_steps),
            confidence=0.95,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_top_active_goal(goals: list[GoalHypothesis] | None) -> GoalHypothesis | None:
        if not goals:
            return None
        active = [g for g in goals if g.state in (GoalState.HYPOTHESIZED, GoalState.ACTIVE)
                  and g.category != GoalCategory.UNKNOWN]
        if not active:
            return None
        return max(active, key=lambda g: g.confidence)

    @staticmethod
    def _action_for_goal(goal: GoalHypothesis, patient_state: PatientState | None) -> CognitiveAction:
        """Map a goal category to an appropriate cognitive action."""
        if goal.category == GoalCategory.SEARCH:
            return CognitiveAction(
                action_type=CognitiveActionType.RETRIEVE_MEMORY,
                reasoning_path="",
                confidence=goal.confidence,
                metadata={"goal": goal.name},
            )
        if goal.category == GoalCategory.MEDICAL:
            return CognitiveAction(
                action_type=CognitiveActionType.SPEAK,
                reasoning_path="",
                confidence=goal.confidence,
                suggested_message=None,  # Let care policy generate message
                metadata={"goal": goal.name, "category": "MEDICAL"},
            )
        if goal.category == GoalCategory.SOCIAL:
            return CognitiveAction(
                action_type=CognitiveActionType.SPEAK,
                reasoning_path="",
                confidence=goal.confidence,
                metadata={"goal": goal.name, "category": "SOCIAL"},
            )
        # Default for any other goal
        return CognitiveAction(
            action_type=CognitiveActionType.SPEAK,
            reasoning_path="",
            confidence=goal.confidence,
            metadata={"goal": goal.name},
        )
