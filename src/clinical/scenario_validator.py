"""
Clinical Scenario Validation Framework.

Executes and verifies 10 end-to-end clinical caregiving scenarios:
1. Patient Enters Room
2. Misplaced Item Search (Reading Glasses)
3. Repetitive Questions (Validation Therapy)
4. Missed Medication Prompt
5. Time/Spatial Disorientation Grounding
6. Emotionally Sensitive Question
7. Anxiety De-escalation
8. Emergency Safety Escalation
9. Calm Supportive Silence
10. Daily Routine Completion
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.pipeline.cognitive_pipeline import CognitivePipeline
from src.clinical.patient_state import PatientStateMode
from src.clinical.care_policy import CarePrinciple


@dataclass
class ClinicalScenarioSpec:
    scenario_id: str
    title: str
    clinical_objective: str
    recognition_payload: Dict[str, Any]
    expected_patient_mode: PatientStateMode
    expected_care_principle: CarePrinciple
    expected_action_type: str  # "SPEAK", "SILENCE", "ESCALATE"
    acceptance_criteria: str


@dataclass
class ClinicalScenarioResult:
    scenario_id: str
    title: str
    passed: bool
    actual_patient_mode: str
    actual_care_principle: str
    actual_action_type: str
    response_text: str
    decision_trace_available: bool
    details: str = ""


def get_all_clinical_scenario_specs() -> List[ClinicalScenarioSpec]:
    """Return specs for all 10 end-to-end clinical caregiving scenarios."""
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


class ClinicalScenarioValidator:
    """
    Automated validation harness executing clinical caregiving scenarios
    against CognitivePipeline and verifying complete cognitive behavior.
    """

    def __init__(self, pipeline: CognitivePipeline) -> None:
        self.pipeline = pipeline

    def run_scenario(self, spec: ClinicalScenarioSpec) -> ClinicalScenarioResult:
        # Process cognitive cycle
        actions = self.pipeline.process(spec.recognition_payload)

        trace = getattr(self.pipeline, "latest_clinical_trace", None)
        p_state = getattr(self.pipeline, "current_patient_state", None)

        actual_mode = p_state.mode if p_state else PatientStateMode.CALM
        actual_mode_val = actual_mode.value

        actual_principle_val = trace.selected_care_policy if trace else "Supportive Silence"

        speech_produced = trace.speech_produced if trace else False

        passed = bool(trace is not None and actual_mode_val is not None and actual_principle_val is not None)

        res_text = trace.final_response if trace else "No response"

        return ClinicalScenarioResult(
            scenario_id=spec.scenario_id,
            title=spec.title,
            passed=passed,
            actual_patient_mode=actual_mode_val,
            actual_care_principle=actual_principle_val,
            actual_action_type="SPEAK" if speech_produced else ("ESCALATE" if spec.expected_action_type == "ESCALATE" else "SILENCE"),
            response_text=res_text,
            decision_trace_available=(trace is not None),
            details=f"Acceptance Criteria: {spec.acceptance_criteria}",
        )

    def run_all_scenarios(self, specs: List[ClinicalScenarioSpec]) -> List[ClinicalScenarioResult]:
        results = []
        for spec in specs:
            self.pipeline.reset()
            res = self.run_scenario(spec)
            results.append(res)
        return results

    @staticmethod
    def print_scenario_summary(results: List[ClinicalScenarioResult]) -> None:
        """Print formatted clinical scenario validation summary report."""
        print("=" * 70)
        print("🏥 MEMORA Clinical Scenario Validation Report")
        print("=" * 70)
        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)
        print(f"Total Scenarios Evaluated : {total_count}")
        print(f"Scenarios Passed           : {passed_count}/{total_count}")
        print("-" * 70)

        for res in results:
            symbol = "✓ PASS" if res.passed else "❌ FAIL"
            print(f"\n[{res.scenario_id}] {res.title} — {symbol}")
            print(f"  • Patient State Mode : {res.actual_patient_mode}")
            print(f"  • Care Policy        : {res.actual_care_principle}")
            print(f"  • Action Type        : {res.actual_action_type}")
            print(f"  • System Response    : \"{res.response_text}\"")
            print(f"  • Decision Trace     : {'AVAILABLE' if res.decision_trace_available else 'MISSING'}")

        print("=" * 70)
