"""
Samsung Anchor — Goal Reasoner.

Defines the GoalReasoner Protocol (the swap-point for future ML/LLM inference)
and the default HeuristicGoalReasoner.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Protocol

from src.cognition.context.models import CognitiveContext
from src.cognition.goals.models import (
    EvidenceSignal,
    GoalCategory,
    GoalHypothesis,
)


class GoalReasoner(Protocol):
    """
    The pluggable inference algorithm.
    Future implementations: LLM-backed, RL-agent, neurosymbolic.
    """

    def infer(self, context: CognitiveContext) -> List[GoalHypothesis]:
        """Return a list of goal hypotheses for the current context."""
        ...


class HeuristicGoalReasoner:
    """
    Rule-based goal reasoner that maps context signals to goal hypotheses.

    This exists to *validate the architecture*, not to be the final
    inference engine.  The GoalReasoner Protocol guarantees that any
    future algorithm can replace this with zero pipeline changes.
    """

    def infer(self, context: CognitiveContext) -> List[GoalHypothesis]:
        now = datetime.now()
        hypotheses: List[GoalHypothesis] = []

        # ------------------------------------------------------------------
        # 1. Temporal + Memory signals → Medical goals
        # ------------------------------------------------------------------
        if context.memory and context.memory.memories:
            for mem in context.memory.memories:
                summary_lower = mem.summary.lower()
                if any(kw in summary_lower for kw in ("medicine", "pill", "medication", "heart")):
                    evidence = [
                        EvidenceSignal(
                            source="MemoryProvider",
                            signal=f"medical_keyword_in={mem.memory_id}",
                            weight=0.40,
                            timestamp=now,
                        )
                    ]
                    # Morning boosts medication goal
                    if context.temporal and context.temporal.time_of_day == "Morning":
                        evidence.append(
                            EvidenceSignal(
                                source="TemporalProvider",
                                signal="time_of_day=Morning",
                                weight=0.30,
                                timestamp=now,
                            )
                        )
                    # Known identity adds weak evidence
                    if context.identity and context.identity.is_known:
                        evidence.append(
                            EvidenceSignal(
                                source="IdentityProvider",
                                signal=f"known_person={context.identity.name}",
                                weight=0.10,
                                timestamp=now,
                            )
                        )

                    h = GoalHypothesis(
                        name="Medication Routine",
                        category=GoalCategory.MEDICAL,
                        confidence=0.0,
                        supporting_evidence=evidence,
                    )
                    h.recalculate_confidence()
                    hypotheses.append(h)
                    break  # one medical goal per cycle

        # ------------------------------------------------------------------
        # 2. Temporal signals → Daily Routine goals
        # ------------------------------------------------------------------
        if context.temporal:
            tod = context.temporal.time_of_day
            evidence = [
                EvidenceSignal(
                    source="TemporalProvider",
                    signal=f"time_of_day={tod}",
                    weight=0.20,
                    timestamp=now,
                )
            ]
            routine_map = {
                "Morning": "Preparing Breakfast",
                "Afternoon": "Afternoon Activity",
                "Evening": "Evening Wind-Down",
                "Night": "Preparing for Sleep",
            }
            goal_name = routine_map.get(tod, "Daily Routine")

            h = GoalHypothesis(
                name=goal_name,
                category=GoalCategory.DAILY_ROUTINE,
                confidence=0.0,
                supporting_evidence=evidence,
            )
            h.recalculate_confidence()
            hypotheses.append(h)

        # ------------------------------------------------------------------
        # 3. Identity signals → Social goals
        # ------------------------------------------------------------------
        if context.identity and context.identity.is_known:
            evidence = [
                EvidenceSignal(
                    source="IdentityProvider",
                    signal=f"person_present={context.identity.name}",
                    weight=0.15,
                    timestamp=now,
                )
            ]
            h = GoalHypothesis(
                name=f"Social Interaction with {context.identity.name}",
                category=GoalCategory.SOCIAL,
                confidence=0.0,
                supporting_evidence=evidence,
            )
            h.recalculate_confidence()
            hypotheses.append(h)

        # ------------------------------------------------------------------
        # 4. Always include an Unknown goal to represent residual uncertainty
        # ------------------------------------------------------------------
        if not hypotheses:
            hypotheses.append(
                GoalHypothesis(
                    name="Unknown",
                    category=GoalCategory.UNKNOWN,
                    confidence=0.15,
                )
            )
        else:
            # Add Unknown as the catch-all with residual probability
            total = sum(h.confidence for h in hypotheses)
            residual = max(0.05, 1.0 - total)
            hypotheses.append(
                GoalHypothesis(
                    name="Unknown",
                    category=GoalCategory.UNKNOWN,
                    confidence=min(0.50, residual),
                )
            )

        return hypotheses
