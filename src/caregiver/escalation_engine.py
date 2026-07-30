"""
MEMORA Clinical Escalation Evaluation Engine.

Evaluates timeline event streams against predefined deterministic policy rules to recommend
clinical escalation levels (NONE, LOW, MODERATE, HIGH, URGENT) without sending alerts or push messages.
"""

from __future__ import annotations

import threading
from typing import List, Tuple

from src.caregiver.caregiver_models import EscalationLevel, TimelineEvent, TimelineEventType


class EscalationEngine:
    """
    Thread-safe clinical escalation policy evaluator.
    Evaluates verified timeline event statistics against clinical risk thresholds.
    """

    def __init__(self) -> None:
        self._evaluation_history: List[Tuple[EscalationLevel, List[str]]] = []
        self._lock = threading.Lock()

    def evaluate_escalation(self, events: List[TimelineEvent]) -> Tuple[EscalationLevel, List[str]]:
        """
        Evaluate timeline events against clinical escalation policies.
        Returns (EscalationLevel, List[supporting_policy_rules]).
        """
        rules_triggered: List[str] = []
        highest = EscalationLevel.NONE

        with self._lock:
            # Rule 1: Safety Events
            safety_events = [e for e in events if e.event_type == TimelineEventType.SAFETY_EVENT]
            if len(safety_events) >= 2:
                highest = EscalationLevel.URGENT
                rules_triggered.append(
                    f"Policy Rule #1: Multiple safety events ({len(safety_events)}) recorded -> URGENT escalation."
                )
            elif len(safety_events) == 1:
                if highest != EscalationLevel.URGENT:
                    highest = EscalationLevel.HIGH
                rules_triggered.append(
                    "Policy Rule #1: Single safety event recorded -> HIGH escalation."
                )

            # Rule 2: Disorientation & Confusion Frequency
            confusion_events = [
                e for e in events
                if e.event_type in (TimelineEventType.DISORIENTATION, TimelineEventType.REASSURANCE)
            ]
            if len(confusion_events) >= 5:
                if highest not in (EscalationLevel.URGENT, EscalationLevel.HIGH):
                    highest = EscalationLevel.HIGH
                rules_triggered.append(
                    f"Policy Rule #2: Frequent confusion events ({len(confusion_events)}) -> HIGH escalation."
                )
            elif len(confusion_events) >= 3:
                if highest in (EscalationLevel.NONE, EscalationLevel.LOW):
                    highest = EscalationLevel.MODERATE
                rules_triggered.append(
                    f"Policy Rule #2: Moderate confusion events ({len(confusion_events)}) -> MODERATE escalation."
                )

            # Rule 3: Caregiver Interventions & Misplaced Item Frequency
            caregiver_events = [e for e in events if e.event_type == TimelineEventType.CAREGIVER_INTERVENTION]
            obj_events = [e for e in events if e.event_type == TimelineEventType.OBJECT_ASSISTANCE]

            if len(caregiver_events) >= 3 or len(obj_events) >= 5:
                if highest == EscalationLevel.NONE:
                    highest = EscalationLevel.LOW
                rules_triggered.append(
                    f"Policy Rule #3: Elevated caregiver interventions ({len(caregiver_events)}) or object searches ({len(obj_events)}) -> LOW escalation."
                )

            if not rules_triggered:
                rules_triggered.append(
                    "Policy Rule #0: All patient events within normal baseline parameters -> NONE escalation."
                )

            res = (highest, rules_triggered)
            self._evaluation_history.append(res)
            return res

    def get_evaluation_history(self) -> List[Tuple[EscalationLevel, List[str]]]:
        """Return history of performed escalation evaluations."""
        with self._lock:
            return list(self._evaluation_history)

    def clear(self) -> None:
        """Clear evaluation history."""
        with self._lock:
            self._evaluation_history.clear()
