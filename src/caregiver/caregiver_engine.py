"""
MEMORA Central Caregiver Engine.

Public façade coordinating PatientTimeline, TrendAnalysisEngine, EscalationEngine,
and ClinicalSummaryGenerator. Serves as the authoritative provider of caregiver insights.
"""

from __future__ import annotations

import hashlib
import json
import threading
from typing import Any, Dict, List, Optional, Tuple

from src.caregiver.caregiver_models import (
    CaregiverSnapshot,
    CaregiverSummary,
    EscalationLevel,
    TimelineEvent,
    TimelineEventType,
    TrendReport,
)
from src.caregiver.clinical_summary import ClinicalSummaryGenerator
from src.caregiver.escalation_engine import EscalationEngine
from src.caregiver.patient_timeline import PatientTimeline
from src.caregiver.trend_analysis import TrendAnalysisEngine


class CaregiverEngine:
    """
    Unified public façade for Caregiver Intelligence & Clinical Oversight.
    Coordinates event ingestion, timeline generation, longitudinal trends, and clinical summary reports.
    """

    def __init__(self) -> None:
        self.timeline = PatientTimeline()
        self.trend_analyzer = TrendAnalysisEngine()
        self.escalation_engine = EscalationEngine()
        self.summary_generator = ClinicalSummaryGenerator()

        self._summaries: List[CaregiverSummary] = []
        self._lock = threading.RLock()

    def ingest_event(
        self,
        event_type: TimelineEventType,
        description: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TimelineEvent:
        """
        Record a verified patient timeline event into the chronological timeline repository.
        """
        return self.timeline.add_event(
            event_type=event_type,
            description=description,
            session_id=session_id,
            metadata=metadata,
        )

    def build_timeline(
        self,
        period: str = "DAILY",
        session_id: Optional[str] = None,
    ) -> List[TimelineEvent]:
        """
        Retrieve timeline events matching period or session filter.
        """
        if session_id:
            return self.timeline.get_session_timeline(session_id)
        if period.upper() == "WEEKLY":
            return self.timeline.get_weekly_timeline()
        return self.timeline.get_daily_timeline()

    def analyze_trends(
        self,
        metric: str = "CONFUSION",
        window: str = "7_DAYS",
    ) -> TrendReport:
        """
        Perform longitudinal trend analysis across recorded events for a given metric.
        """
        events = self.timeline.get_all_events()
        return self.trend_analyzer.analyze_trend(events, metric=metric, window=window)

    def generate_summary(
        self,
        patient_id: str = "default-patient",
        period: str = "DAILY",
    ) -> CaregiverSummary:
        """
        Synthesize a CaregiverSummary for the specified patient and period.
        """
        events = self.timeline.get_all_events()
        summary = self.summary_generator.generate_summary(patient_id, events, period=period)

        with self._lock:
            self._summaries.append(summary)
            return summary

    def evaluate_escalation(self) -> Tuple[EscalationLevel, List[str]]:
        """
        Evaluate clinical escalation policies against current timeline events.
        """
        events = self.timeline.get_all_events()
        return self.escalation_engine.evaluate_escalation(events)

    def get_summary_history(self) -> List[CaregiverSummary]:
        """Return all summaries generated during session lifecycle."""
        with self._lock:
            return list(self._summaries)

    def get_recent_events(self, limit: int = 5) -> List[TimelineEvent]:
        """Return the most recent timeline events up to limit."""
        events = self.timeline.get_all_events()
        return events[-limit:] if events else []

    def get_safety_events(self) -> List[TimelineEvent]:
        """Return all safety-related timeline events."""
        events = self.timeline.get_all_events()
        return [e for e in events if e.is_safety_related()]

    def explain(self) -> str:
        """
        Return a human-readable explanation of caregiver oversight metrics and escalation rules.
        """
        summary = self.generate_summary()
        highest, rules = self.evaluate_escalation()
        return (
            f"Caregiver Oversight Summary [Patient: {summary.patient_id}]\n"
            f"Escalation Rating: `{highest.value}` | Total Assistance Events: {summary.assistance_events}\n"
            f"Supporting Rules: {'; '.join(rules)}"
        )

    def compute_checksum(self) -> str:
        """Compute SHA256 checksum over recorded events and summaries."""
        with self._lock:
            data = {
                "events": len(self.timeline.get_all_events()),
                "summaries": len(self._summaries),
            }
            raw = json.dumps(data, sort_keys=True).encode("utf-8")
            return hashlib.sha256(raw).hexdigest()[:16]

    def snapshot(self) -> CaregiverSnapshot:
        """Generate point-in-time CaregiverSnapshot."""
        events = self.timeline.get_all_events()
        highest, _ = self.escalation_engine.evaluate_escalation(events)
        with self._lock:
            total_evts = len(events)
            sums_cnt = len(self._summaries)
            chk = self.compute_checksum()

            return CaregiverSnapshot(
                total_events_count=total_evts,
                summaries_generated_count=sums_cnt,
                highest_escalation=highest,
                checksum=chk,
            )

    def reset(self) -> None:
        """Reset internal timeline repository and engine state."""
        with self._lock:
            self.timeline.clear()
            self._summaries.clear()
            self.trend_analyzer.clear()
            self.escalation_engine.clear()
            self.summary_generator.clear()
