from src.cognition.assistance.history import ConfidenceHistory
from src.cognition.assistance.models import AssistanceLevel
from src.cognition.assistance.policy_engine import AssistancePolicyEngine
from src.cognition.context.providers.assistance import AssistanceContextProvider
from src.interaction.events import PresenceEvent, PresenceEventType


def test_assistance_level_enum_properties():
    assert AssistanceLevel.LEVEL_0.label == "Level 0: Observe"
    assert AssistanceLevel.LEVEL_1.label == "Level 1: Encourage"
    assert AssistanceLevel.LEVEL_2.label == "Level 2: Gentle Hint"
    assert AssistanceLevel.LEVEL_3.label == "Level 3: Context Restoration"
    assert AssistanceLevel.LEVEL_4.label == "Level 4: Direct Assistance"
    assert AssistanceLevel.LEVEL_5.label == "Level 5: Safety Intervention"

    assert AssistanceLevel.LEVEL_0.name_simple == "Observe"
    assert AssistanceLevel.LEVEL_5.name_simple == "Safety Intervention"


def test_confidence_history_logging():
    history = ConfidenceHistory()
    event = history.log_event("Face_1", AssistanceLevel.LEVEL_2, "Goal active")

    assert event.person_id == "Face_1"
    assert event.level == AssistanceLevel.LEVEL_2
    assert len(history.get_recent_events("Face_1")) == 1
    assert history.get_last_event_for_person("Face_1") == event


def test_policy_engine_evaluation_levels():
    history = ConfidenceHistory()
    engine = AssistancePolicyEngine(history=history)

    event = PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="Face_1",
        name="Sarah",
        relationship="Daughter",
    )

    # 1. Level 3 Context Restoration for recognized person
    ctx = engine.evaluate_level(event, has_known_memories=True)
    assert ctx.level == AssistanceLevel.LEVEL_3
    assert ctx.level_code == 3

    # 2. Escalation to Level 4 Direct Assistance if unresolved
    ctx_escalated = engine.evaluate_level(event, has_known_memories=True)
    assert ctx_escalated.level == AssistanceLevel.LEVEL_4
    assert ctx_escalated.escalation_triggered is True

    # 3. Level 5 Safety Intervention on critical medical commitment
    ctx_safety = engine.evaluate_level(
        event, has_medical_commitment=True, has_known_memories=True
    )
    assert ctx_safety.level == AssistanceLevel.LEVEL_5
    assert ctx_safety.level_code == 5


def test_assistance_context_provider():
    provider = AssistanceContextProvider()
    assert provider.name == "AssistanceContextProvider"
    assert provider.capability_domain == "assistance"

    event = PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="Face_1",
        name="Sarah",
        relationship="Daughter",
    )

    response = provider.fetch_context(event)
    assert response is not None
    assert response.domain == "assistance"
    assert response.data.level_code in [0, 1, 2, 3, 4, 5]
