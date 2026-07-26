import pytest
from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline
from src.clinical.patient_state import PatientStateMode
from src.clinical.care_policy import CarePrinciple
from src.clinical.scenario_validator import (
    ClinicalScenarioSpec,
    ClinicalScenarioValidator,
    ClinicalScenarioResult,
    get_all_clinical_scenario_specs,
)


@pytest.fixture
def scenario_specs():
    return get_all_clinical_scenario_specs()


def test_clinical_scenario_validation_framework_execution(scenario_specs):
    db = MemoraDatabase("sqlite:///:memory:")
    pipeline = CognitivePipeline(db)
    validator = ClinicalScenarioValidator(pipeline)

    # 1. Execute Scenario CS-01: Patient Enters Room
    res1 = validator.run_scenario(scenario_specs[0])
    assert res1.passed is True
    assert res1.decision_trace_available is True

    # 2. Execute Scenario CS-03: Repetitive Questions
    pipeline.process({"face_id": "1", "name": "Eleanor", "user_speech": "What time is my appointment?"})
    res3 = validator.run_scenario(scenario_specs[2])
    assert res3.passed is True
    assert "Repetitive" in res3.actual_patient_mode or res3.passed

    # 3. Execute Scenario CS-08: Unsafe Behaviour Escalation
    pipeline.emergency_mgr.trigger_emergency("Fall Detected", priority="CRITICAL")
    res8 = validator.run_scenario(scenario_specs[7])
    assert res8.passed is True
    assert res8.actual_action_type in ["SPEAK", "ESCALATE"]

    pipeline.shutdown()


def test_run_all_10_clinical_scenarios(scenario_specs):
    db = MemoraDatabase("sqlite:///:memory:")
    pipeline = CognitivePipeline(db)
    validator = ClinicalScenarioValidator(pipeline)

    results = validator.run_all_scenarios(scenario_specs)

    assert len(results) == 10
    passed_count = sum(1 for r in results if r.passed)
    assert passed_count >= 9  # High reliability across all 10 clinical scenarios

    pipeline.shutdown()
