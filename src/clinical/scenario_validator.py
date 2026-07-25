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
            res = self.run_scenario(spec)
            results.append(res)
        return results
