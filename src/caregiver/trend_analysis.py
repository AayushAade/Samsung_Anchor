"""
MEMORA Longitudinal Trend Analysis Engine.

Analyzes longitudinal patient behavioral patterns (confusion frequency, routine adherence,
repeated questions) deterministically without machine learning or predictive forecasting.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from src.caregiver.caregiver_models import TimelineEvent, TimelineEventType, TrendReport


class TrendAnalysisEngine:
    """
    Thread-safe longitudinal trend calculation provider.
    Calculates deterministic metric variations over observation windows.
    """

    def __init__(self) -> None:
        self._trend_history: List[TrendReport] = []
        self._lock = threading.Lock()

    def analyze_trend(
        self,
        events: List[TimelineEvent],
        metric: str = "CONFUSION",
        window: str = "7_DAYS",
    ) -> TrendReport:
        """
        Perform a deterministic trend analysis across event history.
        Evaluates metrics against baseline counts without predictive forecasting.
        """
        metric_upper = metric.upper()
        evidence: List[str] = []
        recommendations: List[str] = []
        direction = "STABLE"

        with self._lock:
            # Filter relevant events based on metric
            if "CONFUSION" in metric_upper or "DISORIENTATION" in metric_upper:
                matched = [
                    e for e in events
                    if e.event_type in (TimelineEventType.DISORIENTATION, TimelineEventType.REASSURANCE)
                ]
                count = len(matched)
                evidence.append(f"Observed {count} disorientation/reassurance event(s) in {window}.")

                if count >= 4:
                    direction = "INCREASING"
                    recommendations.append("Consider scheduling a clinical review of orientation cues.")
                elif count == 0:
                    direction = "STABLE"
                    recommendations.append("Confusion events remain low and stable.")

            elif "ROUTINE" in metric_upper:
                matched = [e for e in events if e.event_type == TimelineEventType.ROUTINE_COMPLETION]
                count = len(matched)
                evidence.append(f"Observed {count} completed routine step(s) in {window}.")

                if count >= 3:
                    direction = "STABLE"
                    recommendations.append("Maintain current step-by-step daily routine guidance.")
                else:
                    direction = "DECREASING"
                    recommendations.append("Review morning and evening routine adherence with caregiver.")

            elif "OBJECT" in metric_upper:
                matched = [e for e in events if e.event_type == TimelineEventType.OBJECT_ASSISTANCE]
                count = len(matched)
                evidence.append(f"Observed {count} object assistance search request(s) in {window}.")

                if count >= 3:
                    direction = "INCREASING"
                    recommendations.append(
                        "Ensure frequently misplaced items (glasses, keys) remain in fixed locations."
                    )
                else:
                    direction = "STABLE"
                    recommendations.append("Misplaced item searches remain stable.")

            else:
                count = len(events)
                evidence.append(f"Analyzed {count} total timeline event(s) in {window}.")
                recommendations.append("Continue standard clinical observation.")

            report = TrendReport(
                metric=metric_upper,
                observation_window=window,
                trend_direction=direction,
                supporting_evidence=evidence,
                confidence=1.0,
                recommendations=recommendations,
            )

            self._trend_history.append(report)
            return report

    def get_latest_trend(self, metric: str) -> Optional[TrendReport]:
        """Return the most recently computed trend report for metric."""
        metric_upper = metric.upper()
        with self._lock:
            for report in reversed(self._trend_history):
                if report.metric == metric_upper:
                    return report
            return None

    def get_trend_history(self) -> List[TrendReport]:
        """Return history of performed trend analyses."""
        with self._lock:
            return list(self._trend_history)

    def clear(self) -> None:
        """Clear trend history."""
        with self._lock:
            self._trend_history.clear()
