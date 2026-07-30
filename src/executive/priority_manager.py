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

from typing import List, Optional

from src.executive.executive_models import Goal, GoalType


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
