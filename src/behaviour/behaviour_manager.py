"""
MEMORA Behaviour Intelligence Manager.

Central coordinator orchestrating:
- Routine Learning Engine
- Predictive Assistance Engine
- Cognitive Drift Monitor
- Personalisation Manager
- Behaviour Timeline
- Caregiver Insights Generator

Invoked once per cognitive cycle to record observations, update routines,
compute predictions, and produce observable payload for dashboard streaming.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from src.behaviour.models import ActivityCategory
from src.behaviour.routine_engine import RoutineLearningEngine
from src.behaviour.prediction_engine import PredictiveAssistanceEngine
from src.behaviour.drift_monitor import CognitiveDriftMonitor
from src.behaviour.personalisation_profile import PersonalisationManager
from src.behaviour.behaviour_timeline import BehaviourTimeline
from src.behaviour.caregiver_insights import CaregiverInsightsGenerator
from src.behaviour.simulation_framework import BehaviourSimulationFramework


class BehaviourManager:
    """
    Central orchestrator for the Behaviour Intelligence Platform.
    """

    def __init__(self) -> None:
        self.routine_engine = RoutineLearningEngine(decay_halflife_days=7.0)
        self.prediction_engine = PredictiveAssistanceEngine(self.routine_engine)
        self.drift_monitor = CognitiveDriftMonitor(window_days=30)
        self.personalisation_mgr = PersonalisationManager(patient_id="P1")
        self.timeline = BehaviourTimeline()
        self.insights_generator = CaregiverInsightsGenerator(
            routine_engine=self.routine_engine,
            drift_monitor=self.drift_monitor,
        )
        self.simulator = BehaviourSimulationFramework()
        self._cycle_counter = 0
        self._lock = threading.Lock()

    def update_cycle(
        self,
        event_name: Optional[str] = None,
        location: str = "Living Room",
        user_speech: Optional[str] = None,
        patient_state_mode: str = "Calm",
        time_of_day: str = "Morning",
    ) -> Dict[str, Any]:
        """
        Execute one cycle of behaviour intelligence processing.

        Parameters
        ----------
        event_name : str | None
            Name of person detected or event title.
        location : str
            Active room/location.
        user_speech : str | None
            User speech transcript.
        patient_state_mode : str
            Patient state mode string.
        time_of_day : str
            Current time of day label ("Morning", "Afternoon", "Evening", "Night").

        Returns
        -------
        Dict[str, Any]
            Serialisable behaviour intelligence summary dictionary.
        """
        with self._lock:
            self._cycle_counter += 1

        # 1. Infer activity category and record observation
        cat = ActivityCategory.GENERAL_ACTIVITY
        act_title = "General Interaction"
        if event_name:
            cat = ActivityCategory.VISITOR_INTERACTION
            act_title = f"Visit with {event_name}"
        elif user_speech and any(w in user_speech.lower() for w in ["where", "find", "lost"]):
            cat = ActivityCategory.OBJECT_PLACEMENT
            act_title = "Searching for Misplaced Item"
            self.drift_monitor.record_metric("object_search_frequency", 1.0)
        elif user_speech and any(w in user_speech.lower() for w in ["pill", "medicine", "medication"]):
            cat = ActivityCategory.MEDICATION_ROUTINE
            act_title = "Medication Routine"

        if patient_state_mode in ("Repetitive Queries", "Confused"):
            self.drift_monitor.record_metric("repeated_questions_count", 1.0)

        # Record in Routine Engine
        model = self.routine_engine.record_observation(
            activity_name=act_title,
            category=cat,
            location=location,
            time_of_day=time_of_day,
        )

        # Record in Behaviour Timeline
        self.timeline.record_activity(
            activity_name=act_title,
            location=location,
            duration_mins=15.0,
            stability_score=model.confidence,
        )

        # 2. Compute Predictions
        pred_activity = self.prediction_engine.predict_next_activity()

        # 3. Apply periodic decay
        if self._cycle_counter % 20 == 0:
            self.routine_engine.decay_patterns()

        # 4. Synthesize Summary for Dashboard
        active_routines = self.routine_engine.get_active_routines(min_confidence=0.35)
        drift_metrics = self.drift_monitor.evaluate_trends()
        insights = self.insights_generator.get_latest_insights()

        return {
            "cycle": self._cycle_counter,
            "current_activity": act_title,
            "active_routines_count": len(active_routines),
            "routines": [r.to_dict() for r in active_routines[:3]],
            "next_activity_prediction": pred_activity.to_dict(),
            "drift_metrics": [m.to_dict() for m in drift_metrics],
            "insights_count": len(insights),
            "top_insight": insights[0].to_dict() if insights else None,
            "personalisation": self.personalisation_mgr.to_dict(),
        }

    def get_summary(self) -> Dict[str, Any]:
        """Return serialisable snapshot of behavior intelligence state."""
        return {
            "cycle_count": self._cycle_counter,
            "routines": [r.to_dict() for r in self.routine_engine.get_active_routines()],
            "personalisation": self.personalisation_mgr.to_dict(),
            "timeline_entries": len(self.timeline.get_recent_entries(limit=50)),
        }

    def reset(self) -> None:
        with self._lock:
            self.routine_engine._behaviours.clear()
            self.routine_engine._routines.clear()
            self.routine_engine._initialize_baseline_routines()
            self.drift_monitor._metric_history.clear()
            self.drift_monitor._initialize_default_metrics()
            self.timeline.clear()
            self._cycle_counter = 0
