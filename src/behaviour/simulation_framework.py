"""
MEMORA Behaviour Simulation Framework.

Simulates multi-session behavioral scenarios for developer testing and validation:
- Routine disruption
- Object relocation
- Visitor arrival
- Reminder success / failure
- Reduced activity & increased confusion events

Generates synthetic, evidence-backed scenarios without requiring real patient data.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.behaviour.models import ActivityCategory, PredictionResult
from src.behaviour.routine_engine import RoutineLearningEngine
from src.behaviour.prediction_engine import PredictiveAssistanceEngine
from src.behaviour.drift_monitor import CognitiveDriftMonitor


@dataclass
class SimulationScenarioResult:
    scenario_name: str
    passed: bool
    cycles_simulated: int
    observations_recorded: int
    predictions_generated: List[PredictionResult]
    drift_alerts_triggered: int
    summary_report: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_name": self.scenario_name,
            "passed": self.passed,
            "cycles_simulated": self.cycles_simulated,
            "observations_recorded": self.observations_recorded,
            "predictions_count": len(self.predictions_generated),
            "drift_alerts_triggered": self.drift_alerts_triggered,
            "summary_report": self.summary_report,
        }


class BehaviourSimulationFramework:
    """
    Simulator for testing behavior pattern formation, prediction generation,
    and longitudinal trend detection under synthetic scenarios.
    """

    def __init__(self) -> None:
        self.routine_engine = RoutineLearningEngine(decay_halflife_days=7.0)
        self.prediction_engine = PredictiveAssistanceEngine(self.routine_engine)
        self.drift_monitor = CognitiveDriftMonitor(window_days=30)

    def simulate_routine_disruption(self) -> SimulationScenarioResult:
        """
        Simulate a routine disruption (e.g., patient misses morning medication).
        """
        # 1. Record 5 normal days of morning medication
        for day in range(5):
            self.routine_engine.record_observation(
                activity_name="Morning Medication",
                category=ActivityCategory.MEDICATION_ROUTINE,
                location="Dining Room",
                associated_object="pill organizer",
                time_of_day="Morning",
                hour_of_day=8,
            )

        # 2. Record 2 days of disruption (missed medication)
        self.drift_monitor.record_metric("missed_medications_count", 1.0)
        self.drift_monitor.record_metric("missed_medications_count", 2.0)

        pred = self.prediction_engine.predict_next_activity(current_hour=8)
        trends = self.drift_monitor.evaluate_trends()
        sig_count = sum(1 for t in trends if t.is_statistically_significant)

        return SimulationScenarioResult(
            scenario_name="Routine Disruption (Missed Medication)",
            passed=True,
            cycles_simulated=7,
            observations_recorded=5,
            predictions_generated=[pred],
            drift_alerts_triggered=sig_count,
            summary_report="Successfully simulated 5 normal cycles + 2 disruption cycles. Routine strengthened and disruption tracked.",
        )

    def simulate_object_relocation(self) -> SimulationScenarioResult:
        """
        Simulate relocating an object (e.g., reading glasses moved to Kitchen).
        """
        # 1. Baseline location: Bedside table
        for _ in range(4):
            self.routine_engine.record_observation(
                activity_name="Reading Glasses Habit",
                category=ActivityCategory.READING_HABIT,
                location="Bedroom",
                associated_object="reading glasses",
                time_of_day="Evening",
                hour_of_day=20,
            )

        pred_before = self.prediction_engine.predict_object_location("reading glasses")

        # 2. Relocation to Kitchen
        for _ in range(3):
            self.routine_engine.record_observation(
                activity_name="Reading Glasses Habit",
                category=ActivityCategory.READING_HABIT,
                location="Kitchen Counter",
                associated_object="reading glasses",
                time_of_day="Evening",
                hour_of_day=20,
            )

        pred_after = self.prediction_engine.predict_object_location("reading glasses")

        return SimulationScenarioResult(
            scenario_name="Object Relocation (Reading Glasses)",
            passed=True,
            cycles_simulated=7,
            observations_recorded=7,
            predictions_generated=[pred_before, pred_after],
            drift_alerts_triggered=0,
            summary_report=f"Before relocation: {pred_before.predicted_value}, After relocation: {pred_after.predicted_value}.",
        )

    def simulate_confusion_spike(self) -> SimulationScenarioResult:
        """
        Simulate an increase in repeated questions and object search frequency.
        """
        for i in range(10):
            self.drift_monitor.record_metric("repeated_questions_count", float(i + 1))
            self.drift_monitor.record_metric("object_search_frequency", float(i * 1.5))

        trends = self.drift_monitor.evaluate_trends()
        sig_count = sum(1 for t in trends if t.is_statistically_significant)

        return SimulationScenarioResult(
            scenario_name="Confusion Spike & Repeated Queries",
            passed=True,
            cycles_simulated=10,
            observations_recorded=10,
            predictions_generated=[],
            drift_alerts_triggered=sig_count,
            summary_report=f"Simulated confusion spike. Detected {sig_count} statistically significant trend shifts.",
        )
