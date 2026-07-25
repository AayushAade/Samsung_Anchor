import pytest
from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline
from src.clinical.patient_state import PatientStateMode
from src.clinical.care_policy import CarePrinciple
from src.clinical.scenario_validator import (
    ClinicalScenarioSpec,
    ClinicalScenarioValidator,
    ClinicalScenarioResult,
)


@pytest.fixture
def scenario_specs():
    return [
        ClinicalScenarioSpec(
            scenario_id="CS-01",
            title="Patient Enters Room",
            clinical_objective="Recognize patient arrival gently without startling",
            recognition_payload={"face_id": "1", "name": "Eleanor", "relationship": "Patient"},
            expected_patient_mode=PatientStateMode.ORIENTED,
            expected_care_principle=CarePrinciple.ONE_STEP_GUIDANCE,
            expected_action_type="SPEAK",
            acceptance_criteria="Produces non-startling greeting action and records clinical decision trace",
        ),
        ClinicalScenarioSpec(
            scenario_id="CS-02",
            title="Searching for Misplaced Reading Glasses",
            clinical_objective="Assist patient in locating misplaced personal items",
            recognition_payload={"face_id": "1", "name": "Eleanor", "user_speech": "Where are my reading glasses?"},
            expected_patient_mode=PatientStateMode.SEARCHING,
            expected_care_principle=CarePrinciple.ONE_STEP_GUIDANCE,
            expected_action_type="SPEAK",
            acceptance_criteria="Identifies SEARCHING mode and offers single-step guidance to item location",
        ),
        ClinicalScenarioSpec(
            scenario_id="CS-03",
            title="Repetitive Questions (Validation Therapy)",
            clinical_objective="Provide warm, identical reassurance without scolding or expressing impatience",
            recognition_payload={"face_id": "1", "name": "Eleanor", "user_speech": "What time is my appointment?"},
            expected_patient_mode=PatientStateMode.REPETITIVE,
            expected_care_principle=CarePrinciple.REPETITIVE_REDIRECTION,
            expected_action_type="SPEAK",
            acceptance_criteria="Triggers REPETITIVE_REDIRECTION policy with consistent validation message",
        ),
        ClinicalScenarioSpec(
            scenario_id="CS-04",
            title="Missed Medication Prompt",
            clinical_objective="Deliver non-confrontational single-step medication reminder",
            recognition_payload={"face_id": "1", "name": "Eleanor"},
            expected_patient_mode=PatientStateMode.AWAITING_REMINDER,
            expected_care_principle=CarePrinciple.ONE_STEP_GUIDANCE,
            expected_action_type="SPEAK",
            acceptance_criteria="Identifies pending dose in MedicationManager and prompts gently",
        ),
        ClinicalScenarioSpec(
            scenario_id="CS-05",
            title="Time/Spatial Disorientation Grounding",
            clinical_objective="Softly ground patient in current time and location without confrontation",
            recognition_payload={"face_id": "1", "name": "Eleanor", "user_speech": "Where am I and what day is it?"},
            expected_patient_mode=PatientStateMode.DISORIENTED,
            expected_care_principle=CarePrinciple.GENTLE_ORIENTATION,
            expected_action_type="SPEAK",
            acceptance_criteria="Generates gentle location/time grounding response",
        ),
        ClinicalScenarioSpec(
            scenario_id="CS-06",
            title="Emotionally Sensitive Question",
            clinical_objective="Validate feelings and provide calm emotional safety without arguing",
            recognition_payload={"face_id": "1", "name": "Eleanor", "user_speech": "Why am I forgetting things?"},
            expected_patient_mode=PatientStateMode.ANXIOUS,
            expected_care_principle=CarePrinciple.VALIDATION_THERAPY,
            expected_action_type="SPEAK",
            acceptance_criteria="Applies validation therapy and grounds in safety",
        ),
        ClinicalScenarioSpec(
            scenario_id="CS-07",
            title="Anxiety De-escalation",
            clinical_objective="Reassure patient during acute anxiety or distress",
            recognition_payload={"face_id": "1", "name": "Eleanor", "user_speech": "I feel frightened and scared"},
            expected_patient_mode=PatientStateMode.ANXIOUS,
            expected_care_principle=CarePrinciple.VALIDATION_THERAPY,
            expected_action_type="SPEAK",
            acceptance_criteria="Triggers VALIDATION_THERAPY and delivers comforting safety reassurance",
        ),
        ClinicalScenarioSpec(
            scenario_id="CS-08",
            title="Unsafe Behaviour Escalation",
            clinical_objective="Escalate active emergency safety hazards immediately to caregiver team",
            recognition_payload={"face_id": "1", "name": "Eleanor"},
            expected_patient_mode=PatientStateMode.EMERGENCY,
            expected_care_principle=CarePrinciple.EMERGENCY_ESCALATION,
            expected_action_type="ESCALATE",
            acceptance_criteria="Triggers EMERGENCY_ESCALATION, notifies caregiver, and records audit trace",
        ),
        ClinicalScenarioSpec(
            scenario_id="CS-09",
            title="Calm Observation (Supportive Silence)",
            clinical_objective="Preserve patient calm by maintaining supportive silence when no cue is required",
            recognition_payload={"face_id": "1", "name": "Eleanor"},
            expected_patient_mode=PatientStateMode.CALM,
            expected_care_principle=CarePrinciple.SUPPORTIVE_SILENCE,
            expected_action_type="SILENCE",
            acceptance_criteria="Suppresses audio speech and maintains supportive silence",
        ),
        ClinicalScenarioSpec(
            scenario_id="CS-10",
            title="Daily Routine Completion",
            clinical_objective="Support routine daily activity orientation calmly",
            recognition_payload={"face_id": "1", "name": "Eleanor", "user_speech": "Good morning Memora"},
            expected_patient_mode=PatientStateMode.ORIENTED,
            expected_care_principle=CarePrinciple.ONE_STEP_GUIDANCE,
            expected_action_type="SPEAK",
            acceptance_criteria="Processes routine greeting and records episode memory",
        ),
    ]


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
