"""
Context shown to caregivers or placed in model prompts must not be invented.
"""

from __future__ import annotations

from src.clinical.consent_manager import ConsentManager
from src.cognition.context.providers.assistance import AssistanceContextProvider
from src.cognition.context.providers.continuity import ContinuityContextProvider
from src.interaction.events import PresenceEvent, PresenceEventType


def _event(rel="Daughter"):
    return PresenceEvent(type=PresenceEventType.PERSON_ARRIVED, face_id="2", name="Riya", relationship=rel)


def test_orientation_has_no_invented_activities_outside_demo():
    ctx = ContinuityContextProvider().fetch_context(_event()).data
    assert ctx.recent_activity is None and ctx.upcoming_activity is None
    assert ctx.today_events == []
    assert ctx.routine_stage in ("Morning", "Afternoon", "Evening", "Night")


def test_demo_orientation_still_available_when_requested():
    ctx = ContinuityContextProvider(demo_data=True).fetch_context(_event()).data
    assert ctx.recent_activity and ctx.today_events


def test_daughter_visit_is_not_a_medical_safety_intervention():
    ctx = AssistanceContextProvider().fetch_context(_event()).data
    assert ctx.level_code < 5
    assert ctx.escalation_triggered is False


def test_consent_is_never_assumed():
    assert not any(ConsentManager().get_consent_summary().values())
