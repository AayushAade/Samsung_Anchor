"""
Cognitive Operating System — Cognitive Kernel.

The central reasoning coordinator. Composes Working Memory, Attention Manager,
Decision Engine, and Cognitive Event Graph into a single ``reason()`` method
invoked once per cognitive pipeline cycle.

The kernel NEVER performs perception, memory storage, or speech directly.
It decides WHAT, WHEN, WHY, and in WHAT ORDER — then returns a CognitiveAction
for the pipeline to execute through existing subsystems.
"""

from __future__ import annotations

from typing import Any

from src.cognition.attention.attention_models import AttentionDecision
from src.cognition.context.models import CognitiveContext
from src.cognition.cos.attention_manager import AttentionManager
from src.cognition.cos.decision_engine import DecisionEngine
from src.cognition.cos.event_graph import CognitiveEventGraph
from src.cognition.cos.models import CognitiveAction, CognitiveActionType
from src.cognition.cos.working_memory import WorkingMemory
from src.cognition.goals.models import GoalHypothesis
from src.clinical.patient_state import PatientState


class CognitiveKernel:
    """
    Central Cognitive Kernel.

    Orchestrates one cycle of higher-order reasoning:
        1. Expire stale working memory slots
        2. Update attention focus
        3. Maintain working memory from current context
        4. Invoke decision engine
        5. Record cognitive event graph
        6. Return CognitiveAction

    State Machine:
        IDLE → REASONING → ACTION_SELECTED → IDLE
    """

    def __init__(self) -> None:
        self.working_memory = WorkingMemory()
        self.attention_manager = AttentionManager()
        self.decision_engine = DecisionEngine()
        self.event_graph = CognitiveEventGraph()
        self._cycle_count = 0

    def reason(
        self,
        context: CognitiveContext | None,
        goals: list[GoalHypothesis] | None,
        patient_state: PatientState | None,
        attention_decision: AttentionDecision | None,
    ) -> CognitiveAction:
        """
        Execute one cycle of cognitive reasoning.

        Parameters
        ----------
        context : CognitiveContext | None
            The fused multi-provider context snapshot.
        goals : list[GoalHypothesis] | None
            Current active goal hypotheses.
        patient_state : PatientState | None
            Current patient cognitive/emotional state.
        attention_decision : AttentionDecision | None
            The INTERRUPT/SILENCE output from the CognitiveAttentionEngine.

        Returns
        -------
        CognitiveAction
            The recommended cognitive action with full reasoning trace.
        """
        self._cycle_count += 1

        # ---------------------------------------------------------------
        # Step 1: Garbage-collect expired working memory
        # ---------------------------------------------------------------
        expired_count = self.working_memory.expire_stale()

        # ---------------------------------------------------------------
        # Step 2: Update attention focus lifecycle
        # ---------------------------------------------------------------
        focus = self.attention_manager.update_focus(attention_decision, goals)

        # ---------------------------------------------------------------
        # Step 3: Maintain working memory from current context
        # ---------------------------------------------------------------
        self._update_working_memory(context, goals, patient_state)

        # ---------------------------------------------------------------
        # Step 4: Invoke decision engine
        # ---------------------------------------------------------------
        wm_snapshot = self.working_memory.snapshot()
        action = self.decision_engine.decide(
            context=context,
            goals=goals,
            focus=focus,
            working_memory_snapshot=wm_snapshot,
            patient_state=patient_state,
        )

        # ---------------------------------------------------------------
        # Step 5: Record cognitive event graph
        # ---------------------------------------------------------------
        root_id = self.event_graph.record_event(
            event_type="CognitiveKernel.reason",
            source="CognitiveKernel",
            target="DecisionEngine",
            metadata={"cycle": self._cycle_count, "action": action.action_type.value},
        )

        if focus.target != "None":
            self.event_graph.record_event(
                event_type="AttentionFocusUpdate",
                source="AttentionManager",
                target=focus.target,
                parent_id=root_id,
                metadata={"state": focus.state.value},
            )

        if action.action_type != CognitiveActionType.REMAIN_SILENT:
            self.event_graph.record_event(
                event_type="ActionSelected",
                source="DecisionEngine",
                target=action.action_type.value,
                parent_id=root_id,
                metadata={"reasoning": action.reasoning_path},
            )

        return action

    def get_state_summary(self) -> dict[str, Any]:
        """Return a serialisable summary of the kernel's current cognitive state."""
        return {
            "cycle_count": self._cycle_count,
            "working_memory": self.working_memory.snapshot(),
            "attention_focus": self.attention_manager.get_current_focus().to_dict(),
            "event_graph_size": len(self.event_graph.get_recent_events(limit=500)),
        }

    def reset(self) -> None:
        """Reset all kernel state."""
        self.working_memory.clear()
        self.attention_manager.release_focus()
        self.event_graph.clear()
        self._cycle_count = 0

    # ------------------------------------------------------------------
    # Internal: Context → Working Memory maintenance
    # ------------------------------------------------------------------

    def _update_working_memory(
        self,
        context: CognitiveContext | None,
        goals: list[GoalHypothesis] | None,
        patient_state: PatientState | None,
    ) -> None:
        """
        Populate working memory with relevant short-lived cognitive state.
        """
        # Current identity context
        if context and context.identity and context.identity.is_known:
            self.working_memory.store(
                "current_visitor",
                {
                    "name": context.identity.name,
                    "relationship": context.identity.relationship,
                    "confidence": context.identity.confidence,
                },
                ttl_seconds=120.0,
            )

        # Current conversation topic (from goals)
        if goals:
            active = [g for g in goals if g.state.value in ("HYPOTHESIZED", "ACTIVE")]
            if active:
                top = max(active, key=lambda g: g.confidence)
                self.working_memory.store(
                    "current_conversation",
                    {"topic": top.name, "confidence": top.confidence},
                    ttl_seconds=180.0,
                )

        # Patient state
        if patient_state:
            self.working_memory.store(
                "patient_state",
                {"mode": patient_state.mode.value, "need": patient_state.primary_need},
                ttl_seconds=60.0,
            )
