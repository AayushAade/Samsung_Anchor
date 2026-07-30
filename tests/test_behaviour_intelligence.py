"""
Comprehensive Test Suite for MEMORA Phase 23 — Behaviour Intelligence Platform.

Tests all Phase 23 modules:
1. Behaviour Models & Serialization
2. Routine Learning Engine (Observation accumulation & pattern decay)
3. Predictive Assistance Engine (Transparent evidence-backed predictions)
4. Cognitive Drift Monitor (Longitudinal non-medical trend analysis)
5. Personalisation Manager & Caregiver Overrides
6. Behaviour Timeline (Longitudinal activity stream)
7. Caregiver Insights Generator (Evidence-backed summaries)
8. Behaviour Simulation Framework (Routine disruption, object relocation, confusion spike)
9. Central Behaviour Manager
10. Pipeline Integration
"""

import os
import tempfile
import time
import pytest
from datetime import datetime

from src.behaviour.models import (
    ActivityCategory,
    BehaviourModel,
    RoutinePattern,
    PredictionCategory,
    PredictionResult,
    DriftMetric,
    PersonalisationProfile,
    BehaviourTimelineEntry,
    CaregiverInsight,
)
from src.behaviour.routine_engine import RoutineLearningEngine
from src.behaviour.prediction_engine import PredictiveAssistanceEngine
from src.behaviour.drift_monitor import CognitiveDriftMonitor
from src.behaviour.personalisation_profile import PersonalisationManager
from src.behaviour.behaviour_timeline import BehaviourTimeline
from src.behaviour.caregiver_insights import CaregiverInsightsGenerator
from src.behaviour.simulation_framework import BehaviourSimulationFramework
from src.behaviour.behaviour_manager import BehaviourManager


# ======================================================================
# 1. Behaviour Models Tests
# ======================================================================

class TestBehaviourModels:
    def test_behaviour_model_to_dict(self):
        bm = BehaviourModel(
            behaviour_id="b1",
            name="Morning Tea",
            category=ActivityCategory.MORNING_ROUTINE,
            frequency_count=5,
            confidence=0.80,
        )
        d = bm.to_dict()
        assert d["name"] == "Morning Tea"
        assert d["category"] == "MORNING_ROUTINE"
        assert d["confidence"] == 0.80

    def test_routine_pattern_to_dict(self):
        rp = RoutinePattern(
            routine_id="r1",
            title="Morning Walk",
            category=ActivityCategory.WALKING_HABIT,
            start_hour=7,
            end_hour=8,
            typical_location="Garden",
            confidence=0.85,
        )
        d = rp.to_dict()
        assert d["title"] == "Morning Walk"
        assert d["time_window"] == "07:00 - 08:00"

    def test_prediction_result_to_dict(self):
        pr = PredictionResult(
            category=PredictionCategory.OBJECT_LOCATION,
            predicted_value="Living Room",
            confidence=0.75,
            supporting_evidence=["Observed 3 times"],
            conflicting_evidence=[],
            uncertainty_score=0.25,
            explanation="Likely resting place is Living Room.",
        )
        d = pr.to_dict()
        assert d["category"] == "OBJECT_LOCATION"
        assert d["predicted_value"] == "Living Room"
        assert d["uncertainty_score"] == 0.25


# ======================================================================
# 2. Routine Learning Engine Tests
# ======================================================================

class TestRoutineLearningEngine:
    def test_record_observation_and_promotion(self):
        engine = RoutineLearningEngine(decay_halflife_days=7.0)
        
        # Record 3 observations to trigger routine promotion
        for i in range(3):
            engine.record_observation(
                activity_name="Reading Habit",
                category=ActivityCategory.READING_HABIT,
                location="Living Room",
                associated_object="reading glasses",
                time_of_day="Evening",
                hour_of_day=20,
            )

        routines = engine.get_active_routines(min_confidence=0.30)
        assert len(routines) >= 1
        assert any("Reading Habit" in r.title for r in routines)

    def test_decay_patterns(self):
        engine = RoutineLearningEngine(decay_halflife_days=0.001)  # Very fast decay
        engine.record_observation("Reading", ActivityCategory.READING_HABIT, "Living Room")
        time.sleep(0.02)
        engine.decay_patterns()
        
        behaviours = engine.get_behaviours()
        assert behaviours[0].confidence < 0.35


# ======================================================================
# 3. Predictive Assistance Engine Tests
# ======================================================================

class TestPredictiveAssistanceEngine:
    def test_predict_object_location(self):
        r_engine = RoutineLearningEngine()
        # Seed routine with reading glasses
        for _ in range(3):
            r_engine.record_observation("Reading Glasses Habit", ActivityCategory.READING_HABIT, "Bedroom Desk", associated_object="reading glasses")
        
        pred_engine = PredictiveAssistanceEngine(r_engine)
        pred = pred_engine.predict_object_location("reading glasses")
        
        assert pred.category == PredictionCategory.OBJECT_LOCATION
        assert "Bedroom Desk" in pred.predicted_value
        assert pred.confidence >= 0.50

    def test_predict_next_activity(self):
        r_engine = RoutineLearningEngine()
        pred_engine = PredictiveAssistanceEngine(r_engine)
        
        pred = pred_engine.predict_next_activity(current_hour=8)
        assert pred.category == PredictionCategory.NEXT_ACTIVITY
        assert pred.predicted_value is not None


# ======================================================================
# 4. Cognitive Drift Monitor Tests
# ======================================================================

class TestCognitiveDriftMonitor:
    def test_record_and_evaluate_trends(self):
        monitor = CognitiveDriftMonitor(window_days=30)
        
        # Record observations
        for i in range(5):
            monitor.record_metric("repeated_questions_count", float(i + 1))

        trends = monitor.evaluate_trends()
        assert len(trends) >= 1
        question_metric = next((m for m in trends if m.metric_name == "repeated_questions_count"), None)
        assert question_metric is not None
        assert "repeated_questions_count" in question_metric.evidence_summary


# ======================================================================
# 5. Personalisation Profile Tests
# ======================================================================

class TestPersonalisationManager:
    def test_get_and_update_profile(self):
        mgr = PersonalisationManager(patient_id="P1")
        prof = mgr.get_profile()
        assert prof.patient_id == "P1"

        mgr.update_preferred_object_location("cane", "front hallway")
        assert mgr.get_profile().preferred_object_locations.get("cane") == "front hallway"

    def test_caregiver_overrides(self):
        mgr = PersonalisationManager(patient_id="P1")
        mgr.set_caregiver_override("preferred_verbosity", "DETAILED")
        
        assert mgr.get_effective_setting("preferred_verbosity") == "DETAILED"
        mgr.clear_caregiver_override("preferred_verbosity")
        assert mgr.get_effective_setting("preferred_verbosity") == "CONCISE"


# ======================================================================
# 6. Behaviour Timeline & Caregiver Insights Tests
# ======================================================================

class TestTimelineAndInsights:
    def test_behaviour_timeline(self):
        bt = BehaviourTimeline()
        entry = bt.record_activity("Evening Walk", "Garden", 20.0, 0.90)
        assert entry.entry_id.startswith("btl-")
        assert len(bt.get_recent_entries()) == 1
        
        md = bt.generate_markdown()
        assert "Evening Walk" in md

    def test_caregiver_insights_generator(self):
        r_engine = RoutineLearningEngine()
        drift = CognitiveDriftMonitor()
        gen = CaregiverInsightsGenerator(routine_engine=r_engine, drift_monitor=drift)
        
        insights = gen.generate_insights()
        assert len(insights) >= 1
        assert insights[0].insight_id.startswith("ins-")


# ======================================================================
# 7. Behaviour Simulation Framework Tests
# ======================================================================

class TestBehaviourSimulationFramework:
    def test_simulate_routine_disruption(self):
        sim = BehaviourSimulationFramework()
        res = sim.simulate_routine_disruption()
        assert res.passed is True
        assert "Routine Disruption" in res.scenario_name

    def test_simulate_object_relocation(self):
        sim = BehaviourSimulationFramework()
        res = sim.simulate_object_relocation()
        assert res.passed is True
        assert len(res.predictions_generated) == 2

    def test_simulate_confusion_spike(self):
        sim = BehaviourSimulationFramework()
        res = sim.simulate_confusion_spike()
        assert res.passed is True
        assert res.drift_alerts_triggered >= 1


# ======================================================================
# 8. Central Behaviour Manager Tests
# ======================================================================

class TestBehaviourManager:
    def test_update_cycle(self):
        bm = BehaviourManager()
        summary = bm.update_cycle(event_name="Sarah", location="Living Room", user_speech="where are my glasses?")
        assert summary["cycle"] == 1
        assert summary["current_activity"] == "Visit with Sarah"
        assert "next_activity_prediction" in summary

    def test_get_summary_and_reset(self):
        bm = BehaviourManager()
        bm.update_cycle(event_name="Sarah", location="Living Room")
        bm.reset()
        summary = bm.get_summary()
        assert summary["cycle_count"] == 0


# ======================================================================
# 9. Pipeline Integration Tests
# ======================================================================

class TestPipelineBehaviourIntegration:
    def test_pipeline_instantiates_behaviour_manager(self):
        from src.memory.database import MemoraDatabase
        from src.pipeline.cognitive_pipeline import CognitivePipeline
        
        db = MemoraDatabase(db_path=os.path.join(tempfile.gettempdir(), "test_behaviour_pipeline.sqlite"))
        db.clear()
        pipeline = CognitivePipeline(database=db)
        
        assert hasattr(pipeline, "behaviour_manager")
        
        # Process one cycle
        actions = pipeline.process({"face_id": "face_sarah", "name": "Sarah", "relationship": "Daughter"})
        summary = pipeline.behaviour_manager.get_summary()
        assert summary["cycle_count"] == 1
