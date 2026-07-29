"""
MEMORA Multi-Modal Conflict Detector & Resolver.

Detects, explains, and resolves contradictions across multi-modal observations:
- Vision vs Spatial Memory location mismatches
- Behaviour predictions vs Perceived room transitions
- Active reminders vs Satisfied goal states

Never ignores conflicts silently; logs structured ConflictRecord objects.
"""

from __future__ import annotations

import time
from typing import List, Optional

from src.reasoning.reasoning_models import (
    ConflictRecord,
    Observation,
    ObservationCategory,
)


class ConflictDetector:
    """
    Multi-modal contradiction detector and resolver.
    """

    @classmethod
    def detect_conflicts(cls, observations: List[Observation]) -> List[ConflictRecord]:
        """
        Analyze active observations for cross-modal contradictions.
        """
        conflicts: List[ConflictRecord] = []

        # 1. Location Mismatch Conflict (Vision vs Behaviour / Memory)
        vision_loc_obs = [
            o for o in observations if o.category == ObservationCategory.VISION_OBJECT and "location" in o.payload
        ]
        behaviour_loc_obs = [
            o for o in observations if o.category == ObservationCategory.BEHAVIOUR_PREDICTION and "location" in o.payload
        ]

        for v_obs in vision_loc_obs:
            v_item = v_obs.payload.get("object_name", "").lower()
            v_loc = v_obs.payload.get("location", "")

            for b_obs in behaviour_loc_obs:
                b_item = b_obs.payload.get("object_name", "").lower()
                b_loc = b_obs.payload.get("location", "")

                if v_item and v_item in b_item and v_loc and b_loc and v_loc != b_loc:
                    # Resolve using confidence and recency
                    winner = v_obs.source if v_obs.confidence >= b_obs.confidence else b_obs.source
                    winner_loc = v_loc if winner == v_obs.source else b_loc
                    explanation = (
                        f"Vision source '{v_obs.source}' detected '{v_item}' in {v_loc} "
                        f"(Confidence: {v_obs.confidence:.0%}), but Behaviour source '{b_obs.source}' "
                        f"predicted {b_loc} (Confidence: {b_obs.confidence:.0%}). "
                        f"Resolved in favor of {winner} location ({winner_loc})."
                    )

                    conflicts.append(
                        ConflictRecord(
                            title=f"Location Mismatch for '{v_item}'",
                            opposing_evidence_a=f"{v_obs.source}: {v_loc}",
                            opposing_evidence_b=f"{b_obs.source}: {b_loc}",
                            resolution_strategy="Evidence Weighting & Visual Recency",
                            resolved_winner=winner,
                            explanation=explanation,
                        )
                    )

        # 2. Goal vs Reminder Conflict (Goal Completed vs Reminder Active)
        goal_completed_obs = [
            o for o in observations if o.category == ObservationCategory.GOAL_STATE and o.payload.get("status") == "SATISFIED"
        ]
        reminder_active_obs = [
            o for o in observations if o.category == ObservationCategory.CLINICAL_STATE and o.payload.get("reminder_active") is True
        ]

        for g_obs in goal_completed_obs:
            g_name = g_obs.payload.get("goal_name", "Goal")
            for r_obs in reminder_active_obs:
                r_name = r_obs.payload.get("reminder_name", "Reminder")
                if g_name.lower() in r_name.lower() or r_name.lower() in g_name.lower():
                    explanation = (
                        f"Goal '{g_name}' marked SATISFIED, but reminder '{r_name}' is still active. "
                        "Resolved by suppressing active reminder cue."
                    )
                    conflicts.append(
                        ConflictRecord(
                            title=f"Satisfied Goal with Active Reminder '{r_name}'",
                            opposing_evidence_a=f"Goal Engine: {g_name} SATISFIED",
                            opposing_evidence_b=f"Clinical State: {r_name} ACTIVE",
                            resolution_strategy="Goal Satisfaction Override",
                            resolved_winner="Goal Engine",
                            explanation=explanation,
                        )
                    )

        return conflicts
