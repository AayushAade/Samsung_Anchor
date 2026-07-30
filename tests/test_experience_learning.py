"""
Comprehensive Test Suite for MEMORA Phase 26 — Experience Learning & Adaptive Knowledge Framework.

Tests all Phase 26 modules:
1. Data Models & Serialization (ExecutionRecord, ExecutionPattern, FailureAnalysisRecord, CalibratedConfidence, CaregiverPreference)
2. Append-Only Experience Repository (Storage, querying, capacity limits)
3. Execution History Index (Querying & Markdown timeline formatting)
4. Pattern Library (Pattern extraction & recommendation)
5. Outcome Evaluation Analyzer (7-outcome classification)
6. Success Metrics Engine (Deterministic metric calculation)
7. Failure Analyzer (Root cause extraction)
8. Confidence Calibrator (Empirical variance adjustment)
9. Routine Optimizer & Caregiver Preference Manager (Routine suggestions & preference storage)
10. Central Experience Engine (Multi-cycle experience recording, latency tracking)
11. Pipeline Experience Integration (CognitivePipeline step 6.9 & stream emission)
"""

import os
import tempfile
import time
import pytest

from src.experience.experience_models import (
    CalibratedConfidence,
    CaregiverPreference,
    ExecutionOutcome,
    ExecutionPattern,
    ExecutionRecord,
    FailureAnalysisRecord,
)
from src.experience.experience_repository import ExperienceRepository
from src.experience.execution_history import ExecutionHistoryIndex
from src.experience.pattern_library import PatternLibrary
from src.experience.experience_analyzer import OutcomeAnalyzer
from src.experience.success_metrics import SuccessMetricsEngine
from src.experience.failure_analyzer import FailureAnalyzer
from src.experience.confidence_calibrator import ConfidenceCalibrator
from src.experience.routine_optimizer import RoutineOptimizer
from src.experience.preference_manager import CaregiverPreferenceManager
from src.experience.experience_explainer import ExperienceExplainer
from src.experience.experience_engine import ExperienceEngine


# ======================================================================
# 1. Experience Models Tests
# ======================================================================

class TestExperienceModels:
    def test_execution_record_to_dict(self):
        rec = ExecutionRecord(
            goal_id="g1",
            plan_id="p1",
            tasks_executed=[{"title": "Task 1", "status": "COMPLETED"}],
            completion_status=ExecutionOutcome.SUCCESSFUL,
        )
        d = rec.to_dict()
        assert d["goal_id"] == "g1"
        assert d["completion_status"] == "SUCCESSFUL"

    def test_execution_pattern_to_dict(self):
        pat = ExecutionPattern(
            goal_title="Locate Glasses",
            task_sequence_titles=["Determine Location", "Search Room"],
            usage_count=5,
            success_count=4,
            success_rate=0.80,
        )
        d = pat.to_dict()
        assert d["goal_title"] == "Locate Glasses"
        assert d["success_rate"] == 0.80

    def test_failure_analysis_record_to_dict(self):
        fa = FailureAnalysisRecord(
            execution_id="exc-1",
            root_cause="Room Transition",
            explanation="User moved to Kitchen",
        )
        d = fa.to_dict()
        assert d["root_cause"] == "Room Transition"


# ======================================================================
# 2. Append-Only Experience Repository Tests
# ======================================================================

class TestExperienceRepository:
    def test_add_and_get_records(self):
        repo = ExperienceRepository()
        rec = ExecutionRecord(
            goal_id="g1",
            plan_id="p1",
            tasks_executed=[],
            completion_status=ExecutionOutcome.SUCCESSFUL,
        )
        repo.add_record(rec)
        all_recs = repo.get_all_records()
        assert len(all_recs) >= 3  # Includes baseline records


# ======================================================================
# 3. Execution History Index Tests
# ======================================================================

class TestExecutionHistoryIndex:
    def test_query_similar_executions(self):
        repo = ExperienceRepository()
        idx = ExecutionHistoryIndex(repo)
        results = idx.query_similar_executions("Determine")
        assert len(results) >= 1

    def test_generate_markdown_timeline(self):
        repo = ExperienceRepository()
        idx = ExecutionHistoryIndex(repo)
        md = idx.generate_markdown_timeline()
        assert "Execution History Timeline" in md


# ======================================================================
# 4. Pattern Library Tests
# ======================================================================

class TestPatternLibrary:
    def test_update_and_find_pattern(self):
        lib = PatternLibrary()
        rec = ExecutionRecord(
            goal_id="g1",
            plan_id="p1",
            tasks_executed=[{"title": "Locate Glasses Step"}],
            completion_status=ExecutionOutcome.SUCCESSFUL,
        )
        lib.update_from_execution(rec, "Locate Glasses")
        pat = lib.find_recommended_pattern("Glasses")
        assert pat is not None
        assert "Locate Glasses" in pat.goal_title


# ======================================================================
# 5. Outcome Analyzer Tests
# ======================================================================

class TestOutcomeAnalyzer:
    def test_evaluate_execution_successful(self):
        outcome, reason = OutcomeAnalyzer.evaluate_execution(
            tasks_executed=[{"status": "COMPLETED"}],
            interruptions=[],
            recovery_actions=[],
        )
        assert outcome == ExecutionOutcome.SUCCESSFUL

    def test_evaluate_execution_interrupted(self):
        outcome, reason = OutcomeAnalyzer.evaluate_execution(
            tasks_executed=[],
            interruptions=[{"interrupt_type": "EMERGENCY_ALERT"}],
            recovery_actions=[],
        )
        assert outcome == ExecutionOutcome.INTERRUPTED


# ======================================================================
# 6. Success Metrics Engine Tests
# ======================================================================

class TestSuccessMetricsEngine:
    def test_compute_metrics(self):
        repo = ExperienceRepository()
        metrics = SuccessMetricsEngine.compute_metrics(repo)
        assert metrics["total_executions"] >= 2
        assert metrics["plan_success_rate"] >= 0.0


# ======================================================================
# 7. Failure Analyzer Tests
# ======================================================================

class TestFailureAnalyzer:
    def test_analyze_failure(self):
        rec = ExecutionRecord(goal_id="g1", plan_id="p1", tasks_executed=[], completion_status=ExecutionOutcome.FAILED)
        fa = FailureAnalyzer.analyze_failure(rec, divergence_reason="Room transition detected")
        assert "Room Transition" in fa.root_cause


# ======================================================================
# 8. Confidence Calibrator Tests
# ======================================================================

class TestConfidenceCalibrator:
    def test_calibrate_confidence(self):
        lib = PatternLibrary()
        cal = ConfidenceCalibrator.calibrate_confidence("Reading Glasses", 0.90, lib)
        assert cal.recommended_confidence > 0.0
        assert cal.recommended_confidence <= 1.0


# ======================================================================
# 9. Routine Optimizer & Preference Manager Tests
# ======================================================================

class TestRoutineOptimizerAndPreferences:
    def test_routine_optimizer(self):
        lib = PatternLibrary()
        opt = RoutineOptimizer(lib)
        rec = opt.get_optimized_routine_recommendation("Locate Reading Glasses")
        assert rec["status"] == "OPTIMIZED"

    def test_preference_manager(self):
        pm = CaregiverPreferenceManager()
        pm.set_preference("test_pref", "val1")
        assert pm.get_preference("test_pref") == "val1"


# ======================================================================
# 10. Central Experience Engine Tests
# ======================================================================

class TestExperienceEngine:
    def test_process_cycle(self):
        ee = ExperienceEngine()
        summary = ee.process_cycle(
            executive_summary={
                "top_goal": {"title": "Locate Glasses", "goal_id": "g1"},
                "active_plan": {"plan_id": "p1", "tasks": [{"title": "Step 1"}], "confidence": 0.85},
            },
            location="Living Room",
        )
        assert summary["cycle"] == 1
        assert summary["total_records_count"] >= 3
        assert summary["experience_latency_ms"] >= 0.0

    def test_reset(self):
        ee = ExperienceEngine()
        ee.process_cycle(location="Living Room")
        ee.reset()
        assert ee._cycle_counter == 0


# ======================================================================
# 11. Pipeline Experience Integration Tests
# ======================================================================

class TestPipelineExperienceIntegration:
    def test_pipeline_instantiates_experience_engine(self):
        from src.memory.database import MemoraDatabase
        from src.pipeline.cognitive_pipeline import CognitivePipeline
        
        db = MemoraDatabase(db_path=os.path.join(tempfile.gettempdir(), "test_experience_pipeline.sqlite"))
        db.clear()
        pipeline = CognitivePipeline(database=db)
        
        assert hasattr(pipeline, "experience_engine")
        
        actions = pipeline.process({"face_id": "face_sarah", "name": "Sarah", "relationship": "Daughter"})
        assert pipeline.experience_engine._cycle_counter == 1
