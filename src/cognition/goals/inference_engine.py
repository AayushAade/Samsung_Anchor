"""
Samsung Anchor — Goal Inference Engine.

The orchestrator that wires the GoalReasoner, GoalLifecycleManager,
and GoalRepository into a single coherent step of the cognitive pipeline.
"""

from __future__ import annotations

from typing import List

from src.cognition.context.models import CognitiveContext
from src.cognition.goals.lifecycle import GoalLifecycleManager
from src.cognition.goals.models import GoalHypothesis, GoalState
from src.cognition.goals.reasoner import GoalReasoner, HeuristicGoalReasoner
from src.cognition.goals.repository import GoalRepository


class GoalInferenceEngine:
    """
    Consumes a CognitiveContext and produces an updated set of GoalHypotheses.

    On every cognitive cycle it:
      1. Asks the GoalReasoner for fresh hypotheses.
      2. Merges fresh hypotheses with existing goals in the repository
         (reinforcing or contradicting).
      3. Applies lifecycle evolution (decay, state transitions).
      4. Archives terminal goals.
      5. Returns the current active goal distribution.
    """

    def __init__(
        self,
        reasoner: GoalReasoner | None = None,
    ) -> None:
        self.reasoner: GoalReasoner = reasoner or HeuristicGoalReasoner()
        self.lifecycle = GoalLifecycleManager()
        self.repository = GoalRepository()

    def infer(self, context: CognitiveContext) -> List[GoalHypothesis]:
        """
        Run one cycle of goal reasoning.
        """
        try:
            # 1. Generate fresh hypotheses from context
            fresh = self.reasoner.infer(context)

            # 2. Merge with existing goals
            for hypothesis in fresh:
                existing = self.repository.get_by_name(hypothesis.name)
                if existing and existing.state not in (
                    GoalState.COMPLETED,
                    GoalState.ABANDONED,
                ):
                    # Reinforce: append new evidence to existing goal
                    existing.supporting_evidence.extend(
                        hypothesis.supporting_evidence
                    )
                    existing.contradicting_evidence.extend(
                        hypothesis.contradicting_evidence
                    )
                    existing.recalculate_confidence()
                else:
                    # New goal — insert
                    self.repository.upsert(hypothesis)

            # 3. Apply lifecycle evolution to all active goals
            for goal in self.repository.get_active_goals():
                self.lifecycle.evolve(goal)

            # 4. Archive terminal goals
            self.repository.archive_terminal_goals()

            # 5. Return current distribution
            active = self.repository.get_active_goals()

            # Log
            top = active[0] if active else None
            if top:
                print(
                    f"[GoalInferenceEngine] Top goal: {top.name} "
                    f"({top.confidence:.2f}, {top.state.value})"
                )

            return active

        except Exception as e:
            print(f"[GoalInferenceEngine] Error during goal inference: {e}")
            # Graceful degradation: return whatever is already in the repository
            return self.repository.get_active_goals()
