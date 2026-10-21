"""
Person/caregiver-entered medication schedules and appointments: persistence,
reported (never verified) doses, throttled reminders, and data controls.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import pytest

from src.application.chat import ChatSession
from src.application.factory import build_application
from src.clinical.patient_state import PatientStateMode
from src.memory import user_data
from src.memory.database import MemoraDatabase
from tests.consent_helpers import allow_memory


def _session(path, tmp_path, confirm=lambda p: "DELETE"):
    coord = build_application(live_hardware=False, database=MemoraDatabase(path))
    allow_memory(coord.pipeline)  # care records are personal data: storage consent required
    return ChatSession(coord, log_path=str(tmp_path / "log.txt"), confirm=confirm)


@pytest.fixture
def path(tmp_path):
    return str(tmp_path / "care.sqlite")


def _past_time(minutes=90):
    now = datetime.now()
    if now - now.replace(hour=0, minute=0) < timedelta(minutes=45):
        pytest.skip("too close to midnight for a same-day overdue dose")
    t = max(now - timedelta(minutes=minutes), now.replace(hour=0, minute=0))
    return t.strftime("%H:%M")


def test_schedules_and_appointments_persist(path, tmp_path):
    s = _session(path, tmp_path)
    assert s.handle("/add-medication Aspirin at 08:00, 75 mg").startswith("Saved: Aspirin daily at 08:00")
    when = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d 10:30")
    assert "Saved: Memory clinic" in s.handle(f"/add-appointment Memory clinic on {when} at City Hospital")
    s.close()

    s2 = _session(path, tmp_path)
    assert "Aspirin (75 mg) daily at 08:00" in s2.handle("/medications")
    assert "Memory clinic" in s2.handle("When is my appointment?")
    assert s2.handle("/remove-medication 1") == "Removed Aspirin."
    s2.close()
    assert "No medication schedules" in _session(path, tmp_path).handle("/medications")


def test_invalid_input_is_rejected_without_saving(path, tmp_path):
    s = _session(path, tmp_path)
    assert s.handle("/add-medication Aspirin at noonish").startswith("Please use")
    assert s.handle("/add-appointment Clinic on 2026-13-45 10:30").startswith("That date or time isn't valid")
    assert "No medication schedules" in s.handle("/medications")


def test_reported_dose_is_a_report_and_survives_restart(path, tmp_path):
    s = _session(path, tmp_path)
    s.handle(f"/add-medication Aspirin at {_past_time()}")
    assert "don't have a report" in s.handle("Did I take my aspirin?")
    assert s.handle("I took my aspirin").startswith("Thank you. I've noted that you told me you took your Aspirin")
    s.close()
    s2 = _session(path, tmp_path)
    answer = s2.handle("Did I take my medicine?")
    assert "you told me today that you took your aspirin" in answer.lower()
    assert "I can only go by what you tell me" in answer


def test_overdue_reminder_surfaces_once_in_chat_and_stops_after_report(path, tmp_path):
    s = _session(path, tmp_path)
    s.handle(f"/add-medication Aspirin at {_past_time()}")
    first = s.handle("Hello")
    assert "gentle reminder" in first and "Aspirin" in first
    assert "gentle reminder" not in s.handle("What day is it?")  # throttled
    s.pipeline._last_reminder_at.clear()                       # interval elapsed
    s.handle("I took my aspirin")
    s.pipeline._last_reminder_at.clear()
    assert "gentle reminder" not in s.handle("Hello")           # reported today: no reminder


def test_double_dose_statement_goes_to_safety_not_to_a_report(path, tmp_path):
    s = _session(path, tmp_path)
    s.handle(f"/add-medication Aspirin at {_past_time()}")
    reply = s.handle("I took my pills twice")
    assert "emergency number" in reply
    assert s.pipeline.current_patient_state.mode == PatientStateMode.EMERGENCY
    assert not s.pipeline.medication_mgr.reported_taken_today(s.pipeline.medication_mgr.get_all_schedules()[0].med_id)


def test_export_and_delete_cover_care_data(path, tmp_path):
    s = _session(path, tmp_path)
    s.handle(f"/add-medication Aspirin at {_past_time()}")
    s.handle("I took my aspirin")
    out = tmp_path / "x.json"
    s.handle(f"/export {out}")
    data = json.loads(out.read_text())
    assert [c["title"] for c in data["care_items"]] == ["Aspirin"]
    assert data["care_events"][0]["event"] == "REPORTED_TAKEN"
    assert s.handle("/delete-all").startswith("All your data has been deleted")
    s.close()
    assert "No medication schedules" in _session(path, tmp_path).handle("/medications")
