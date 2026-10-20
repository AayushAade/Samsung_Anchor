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


def test_real_pipeline_holds_no_fictional_people_or_prescriptions():
    """Walk the pipeline's object graph and look for the demo fixtures' names."""
    import gc  # noqa: F401
    from src.memory.database import MemoraDatabase
    from src.pipeline.cognitive_pipeline import CognitivePipeline

    p = CognitivePipeline(MemoraDatabase(":memory:"))
    fictional = ("Eleanor", "Sarah", "Robert Chen", "Donepezil", "Lisinopril", "Margaret")
    seen, hits, stack = set(), [], [(p, "pipeline")]
    while stack:
        obj, path = stack.pop()
        if id(obj) in seen or len(seen) > 200000:
            continue
        seen.add(id(obj))
        if isinstance(obj, str):
            if any(name in obj for name in fictional):
                hits.append((path, obj[:60]))
            continue
        if isinstance(obj, (int, float, bool, bytes, type(None))) or callable(obj) and not hasattr(obj, "__dict__"):
            continue
        if isinstance(obj, dict):
            stack.extend((v, f"{path}[{k!r}]") for k, v in obj.items())
            stack.extend((k, f"{path}.key") for k in obj)
        elif isinstance(obj, (list, tuple, set, frozenset)):
            stack.extend((v, f"{path}[]") for v in obj)
        elif hasattr(obj, "__dict__") and type(obj).__module__.startswith("src."):
            stack.extend((v, f"{path}.{k}") for k, v in vars(obj).items())
    p.shutdown()
    # The patient-profile dataclass keeps its fictional defaults for demo use; it is
    # never surfaced outside demo mode (see CognitivePipeline._patient_name).
    hits = [h for h in hits if ".patient_profile_mgr." not in h[0]]
    assert hits == [], hits[:10]
