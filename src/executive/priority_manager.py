"""
MEMORA Priority Arbitration Engine.

Dynamically arbitrates goal priorities based on:
- Clinical urgency (e.g. medication deadlines)
- Caregiver overrides
- Safety alerts & guardrail statuses
- Reasoning confidence
- Active user interruptions
"""

from __future__ import annotations

from typing import Any, List, Optional

from src.executive.executive_models import Goal, GoalType

import logging
logger = logging.getLogger(__name__)


class PriorityManager:
    """
    Arbitrates and balances goal priorities dynamically.
    """

    @classmethod
    def calculate_effective_priority(
        cls,
        goal: Goal,
        has_caregiver_override: bool = False,
        is_medication_urgent: bool = False,
        is_emergency: bool = False,
    ) -> float:
        """
        Compute effective priority score in range [0.0, 1.0].
        """
        score = goal.priority

        # 1. Strategic goals get baseline boost
        if goal.goal_type == GoalType.STRATEGIC:
            score += 0.10

        # 2. Medication urgency boost
        if is_medication_urgent and "medication" in goal.title.lower():
            score += 0.30

        # 3. Caregiver override boost
        if has_caregiver_override:
            score += 0.25

        # 4. Emergency override
        if is_emergency:
            score = 1.0

        return round(max(0.10, min(1.0, score)), 3)

    @classmethod
    def rank_goals(
        cls,
        goals: List[Goal],
        has_caregiver_override: bool = False,
        is_medication_urgent: bool = False,
        is_emergency: bool = False,
    ) -> List[Goal]:
        """
        Re-arbitrate and rank goals by effective priority descending.
        """
        for g in goals:
            g.priority = cls.calculate_effective_priority(
                g,
                has_caregiver_override=has_caregiver_override,
                is_medication_urgent=is_medication_urgent,
                is_emergency=is_emergency,
            )

        goals.sort(key=lambda g: g.priority, reverse=True)
        return goals

    @classmethod
    def arbitrate_goals(
        cls,
        goals: List[Goal],
        situation: Optional[Any] = None,
        risk_assessment: Optional[Any] = None,
    ) -> Goal:
        """
        Multi-factor utility-weighted goal arbitration (Phase 10 — Objective 3).
        Selects the single top Executive Goal from competing active goal hypotheses.
        """
        if not goals:
            return Goal(title="Default Assistive Orientation", priority=0.50)

        risk_score = getattr(risk_assessment, "score", 0.10) if risk_assessment else 0.10
        risk_level = getattr(getattr(risk_assessment, "level", None), "value", "LOW") if risk_assessment else "LOW"

        def compute_utility(g: Goal) -> float:
            title_lower = g.title.lower()
            
            # 1. Urgency factor
            urgency = 0.40
            if "emergency" in title_lower or risk_level == "CRITICAL":
                urgency = 1.0
            elif "medication" in title_lower or "pill" in title_lower:
                urgency = 0.85
            elif "glasses" in title_lower or "searching" in title_lower:
                urgency = 0.70

            # 2. Safety impact factor
            safety = 0.50
            if risk_level in ("HIGH", "CRITICAL"):
                safety = 0.95
            elif "medication" in title_lower:
                safety = 0.85

            # 3. Clinical priority factor
            clinical = 0.50
            if g.goal_type == GoalType.STRATEGIC:
                clinical += 0.20
            if "medication" in title_lower or "doctor" in title_lower:
                clinical += 0.30

            # 4. Context match factor
            context_match = 0.50
            if situation:
                if getattr(situation, "searching_activity", False) and ("searching" in title_lower or "locate" in title_lower):
                    context_match = 0.90
                if getattr(situation, "pending_medication", False) and "medication" in title_lower:
                    context_match = 0.95

            # 5. Confidence factor
            conf = getattr(g, "confidence", 0.80)

            # Utility Formula: U = 0.25*urgency + 0.30*safety + 0.20*clinical + 0.15*context + 0.10*conf
            utility = (0.25 * urgency) + (0.30 * safety) + (0.20 * clinical) + (0.15 * context_match) + (0.10 * conf)
            return round(utility, 3)

        for g in goals:
            g.priority = compute_utility(g)

        goals.sort(key=lambda g: g.priority, reverse=True)
        logger.debug(f"🎯 [Goal Arbitration] Arbitrated {len(goals)} goals. Top Executive Goal: '{goals[0].title}' (Utility Score: {goals[0].priority})")
        return goals[0]

