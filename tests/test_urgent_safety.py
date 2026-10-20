"""
Urgent-situation handling.

A person telling MEMORA they fell, have chest pain, or cannot breathe must be
directed to human help, never answered with a memory recall, a medication
reminder, or reassurance, and MEMORA must never claim it notified anyone.
"""

from __future__ import annotations

import pytest

from src.clinical.patient_state import PatientStateEvaluator, PatientStateMode
from src.clinical.urgent_safety import UrgentConcernType, detect_urgent_concern
from src.executive.executive_models import RiskLevel, Situation
from src.executive.risk_engine import ExecutiveRiskEngine
from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline


@pytest.mark.parametrize("utterance,expected", [
    ("Help me, I fell", UrgentConcernType.FALL_OR_INJURY),
    ("I've fallen and I can't get up", UrgentConcernType.FALL_OR_INJURY),
    ("My husband fell in the bathroom", UrgentConcernType.FALL_OR_INJURY),
    ("I have chest pain", UrgentConcernType.CHEST_PAIN),
    ("my chest feels tight", UrgentConcernType.CHEST_PAIN),
    ("I can't breathe", UrgentConcernType.BREATHING),
    ("I’m having trouble breathing", UrgentConcernType.BREATHING),
    ("I think I took too many pills", UrgentConcernType.MEDICATION_OVERDOSE),
    ("I took the wrong medicine", UrgentConcernType.MEDICATION_OVERDOSE),
    ("I feel like I'm going to pass out", UrgentConcernType.UNRESPONSIVE_OR_FAINTING),
    ("I cut myself and it is bleeding", UrgentConcernType.BLEEDING),
    ("I want to die", UrgentConcernType.SELF_HARM),
    ("please call an ambulance", UrgentConcernType.HELP_REQUEST),
    ("help me", UrgentConcernType.HELP_REQUEST),
])
def test_detects_urgent_concerns(utterance, expected):
    concern = detect_urgent_concern(utterance)
    assert concern is not None, utterance
    assert concern.concern_type == expected


@pytest.mark.parametrize("utterance", [
    "I fell asleep in the chair",
    "I fell in love with this song",
    "help me find my glasses",
    "can you help me remember my daughter's name",
    "the cup fell off the table",
    "where are my keys",
    "I like green tea",
    "",
    None,
])
def test_benign_utterances_are_not_urgent(utterance):
    assert detect_urgent_concern(utterance) is None


def test_urgent_concern_outranks_medication_and_repetition():
    ev = PatientStateEvaluator()
    ev.evaluate(user_speech="I have chest pain")
    state = ev.evaluate(user_speech="I have chest pain", missed_medications=["Something"])
    assert state.mode == PatientStateMode.EMERGENCY
    assert state.details["urgent_concern"] == UrgentConcernType.CHEST_PAIN.value


def test_speech_outranks_background_medication_state():
    state = PatientStateEvaluator().evaluate(user_speech="Where are my glasses?", missed_medications=["X"])
    assert state.mode == PatientStateMode.SEARCHING


def test_risk_engine_marks_urgent_concern_critical():
    situation = Situation(activity="Sitting", current_location="Kitchen", is_night=False)
    risk = ExecutiveRiskEngine.evaluate_risk(situation, user_speech="I can't breathe")
    assert risk.level == RiskLevel.CRITICAL


@pytest.mark.parametrize("utterance", ["Help me, I fell", "I have chest pain", "I can't breathe",
                                       "I took too many pills"])
def test_pipeline_directs_user_to_human_help(utterance):
    pipeline = CognitivePipeline(MemoraDatabase(":memory:"))
    try:
        result = pipeline.process(user_speech=utterance, location="Living Room", return_dict=True)
    finally:
        pipeline.shutdown()
    reply = (result["speech_response"] or "").lower()
    assert "emergency number" in reply
    assert "can't contact anyone" in reply
    assert "notified" not in reply
    assert "previously you were discussing" not in reply
    assert pipeline.current_patient_state.mode == PatientStateMode.EMERGENCY


def test_configured_number_and_trusted_contact_used_without_claiming_a_call(tmp_path):
    from src.application.chat import ChatSession
    from src.application.factory import build_application
    coord = build_application(live_hardware=False, database=MemoraDatabase(str(tmp_path / "s.sqlite")))
    from tests.consent_helpers import allow_memory
    allow_memory(coord.pipeline)  # saving contacts requires storage consent
    chat = ChatSession(coord, log_path=str(tmp_path / "log"))
    assert chat.handle("/set-emergency-number 112").startswith("Saved.")
    assert chat.handle("/set-trusted-contact Riya 555-0100").startswith("Saved.")
    assert chat.handle("/set-emergency-number call them").startswith("Please give a number")
    reply = chat.handle("I fell and can't get up")
    assert "call 112" in reply and "Riya on 555-0100" in reply
    assert "can't contact anyone myself" in reply
    assert "I have called" not in reply and "notified" not in reply
