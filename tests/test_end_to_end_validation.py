"""
End-to-End Runtime Validation and Integration Tests for MEMORA (Samsung Anchor).
"""

import pytest
from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline
from src.clinical.scenario_validator import ClinicalScenarioValidator, get_all_clinical_scenario_specs
from src.perception.visual_memory_engine import VisualEpisodicMemoryEngine
from src.runtime.runtime import AnchorRuntime
from src.application.factory import build_application


def test_end_to_end_pipeline_cognitive_cycle():
    """Verify complete end-to-end cycle execution from recognition payload to decision trace."""
    db = MemoraDatabase("sqlite:///:memory:")
    pipeline = CognitivePipeline(db)

    # 1. Process recognition payload with speech transcript
    payload = {
        "face_id": "Face_Eleanor_1",
        "name": "Eleanor",
        "relationship": "Patient",
        "user_speech": "Where are my reading glasses?",
    }
    actions = pipeline.process(payload)

    # 2. Verify clinical decision trace recording
    assert pipeline.latest_clinical_trace is not None
    assert pipeline.latest_clinical_trace.patient_state is not None
    assert pipeline.latest_clinical_trace.selected_care_policy is not None

    # 3. Verify interaction action generated
    assert len(actions) > 0
    assert actions[0].message is not None and len(actions[0].message) > 0

    pipeline.shutdown()


def test_end_to_end_10_clinical_scenarios():
    """Verify all 10 clinical caregiving scenarios execute successfully and generate decision traces."""
    db = MemoraDatabase("sqlite:///:memory:")
    pipeline = CognitivePipeline(db)
    validator = ClinicalScenarioValidator(pipeline)

    specs = get_all_clinical_scenario_specs()
    results = validator.run_all_scenarios(specs)

    assert len(results) == 10
    passed_count = sum(1 for r in results if r.passed)
    assert passed_count == 10

    pipeline.shutdown()


def test_visual_episodic_memory_recall():
    """Verify visual episodic memory engine stores and recalls item locations accurately."""
    engine = VisualEpisodicMemoryEngine()

    # Query reading glasses
    res_glasses = engine.recall_object_location("Where are my reading glasses?", "Eleanor")
    assert res_glasses["found"] is True
    assert "coffee table" in res_glasses["response"]

    # Query walking cane
    res_cane = engine.recall_object_location("Have you seen my walking cane?", "Eleanor")
    assert res_cane["found"] is True
    assert "armchair" in res_cane["response"]

    # Query non-existent item
    res_unknown = engine.recall_object_location("Where is my astronaut helmet?", "Eleanor")
    assert res_unknown["found"] is False


def test_runtime_fault_tolerance_and_metrics():
    """Verify runtime manager handles simulated hardware mode and records metrics."""
    coordinator = build_application()
    runtime = AnchorRuntime(coordinator)
    runtime.initialize()
    runtime.start()

    frame1, res1 = runtime.run_once()
    frame2, res2 = runtime.run_once()

    runtime.shutdown()
    assert runtime.cycle_count == 2
    assert runtime.running is False
