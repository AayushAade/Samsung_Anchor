"""
MEMORA Clinical Summary Generator.

Generates concise, structured summaries suitable for family caregivers or clinical staff,
synthesizing completed routines, orientation events, misplaced items, and escalation ratings.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from src.caregiver.caregiver_models import (
    CaregiverSummary,
    EscalationLevel,
    TimelineEvent,
    TimelineEventType,
)
from src.caregiver.escalation_engine import EscalationEngine


class ClinicalSummaryGenerator:
    """
    Thread-safe summary synthesizer for caregiver and clinical reviews.
    Formulates clinical status reports without machine learning or artificial text generation.
    """

    def __init__(self) -> None:
        self.escalation_engine = EscalationEngine()
        self._summary_history: List[CaregiverSummary] = []
        self._lock = threading.Lock()

    def generate_summary(
        self,
        patient_id: str,
        events: List[TimelineEvent],
        period: str = "DAILY",
    ) -> CaregiverSummary:
        """
        Synthesize a list of timeline events into a CaregiverSummary object.
        """
        with self._lock:
            # 1. Calculate event counts
            routines = [e.description for e in events if e.event_type == TimelineEventType.ROUTINE_COMPLETION]
            assistance_cnt = sum(
                1 for e in events
                if e.event_type in (TimelineEventType.CONTEXT_RESTORATION, TimelineEventType.OBJECT_ASSISTANCE)
            )
            confusion_cnt = sum(
                1 for e in events
                if e.event_type in (TimelineEventType.DISORIENTATION, TimelineEventType.REASSURANCE)
            )
            obj_cnt = sum(1 for e in events if e.event_type == TimelineEventType.OBJECT_ASSISTANCE)

            # 2. Evaluate escalation level
            escalation_lvl, _ = self.escalation_engine.evaluate_escalation(events)

            summary = CaregiverSummary(
                patient_id=patient_id,
                reporting_period=period,
                completed_routines=routines,
                assistance_events=assistance_cnt,
                confusion_events=confusion_cnt,
                object_assistance_events=obj_cnt,
                escalation_level=escalation_lvl,
            )

            self._summary_history.append(summary)
            return summary

    def get_summary_history(self) -> List[CaregiverSummary]:
        """Return historical caregiver summaries generated."""
        with self._lock:
            return list(self._summary_history)

    def clear(self) -> None:
        """Clear summary history."""
        with self._lock:
            self._summary_history.clear()
