"""
The clinical scenario harness must report failures, and behaviours it exposed
(unspoken reminders, unannounced visitors, substring object matches) stay fixed.
"""

from __future__ import annotations

import dataclasses

from src.clinical.care_policy import CarePrinciple
from src.clinical.clinical_models import MedicationSchedule
from src.clinical.patient_state import PatientStateMode
from src.clinical.scenario_validator import ClinicalScenarioValidator, get_all_clinical_scenario_specs
from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline


def _pipeline():
    return CognitivePipeline(MemoraDatabase(":memory:"))


def test_all_scenarios_pass_against_their_specifications():
    results = ClinicalScenarioValidator(_pipeline()).run_all_scenarios(get_all_clinical_scenario_specs())
    failed = [(r.scenario_id, r.details) for r in results if not r.passed]
    assert not failed, failed


def test_a_wrong_expectation_is_reported_as_failure():
    spec = dataclasses.replace(get_all_clinical_scenario_specs()[4],  # CS-05 orientation
                               expected_patient_mode=PatientStateMode.EMERGENCY,
                               expected_care_principle=CarePrinciple.EMERGENCY_ESCALATION)
    result = ClinicalScenarioValidator(_pipeline()).run_all_scenarios([spec])[0]
    assert result.passed is False
    assert "Expected:" in result.details


def test_overdue_reminder_spoken_once_per_interval():
    p = _pipeline()
    p.medication_mgr.add_medication(MedicationSchedule(med_id="M", medication_name="Test med", dose="1",
                                                       scheduled_time="00:00", instructions=""))
    p.medication_mgr.grace = p.medication_mgr.grace * 0  # due immediately for the test
    spoken = []
    for _ in range(3):
        acts = p.process({"face_id": "1", "name": "Visitor", "relationship": "Patient"})
        spoken += [a.message for a in acts if "Test med" in (a.message or "")]
    assert len(spoken) == 1
    assert "taken it" in spoken[0] and "you took" not in spoken[0].lower()


def test_known_visitor_announced_unknown_face_not_named():
    p = _pipeline()
    acts = p.process({"face_id": "2", "name": "Riya", "relationship": "Daughter"})
    assert [a.message for a in acts] == ["Hello. Your daughter, Riya, is here."]
    p.reset()
    acts = p.process({"face_id": "9", "name": None})
    assert all("is here" not in (a.message or "") or "Riya" not in a.message for a in acts)


def test_object_names_match_whole_words_only():
    p = _pipeline()
    reply = p.process(user_speech="What time is my appointment?", return_dict=True)["speech_response"]
    assert "hat" not in reply.split()
    assert "appointments" in reply
