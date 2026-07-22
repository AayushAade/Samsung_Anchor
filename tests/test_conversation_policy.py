from src.conversation.conversation_models import ConversationState, ResponseStrategy, SpeakerRole
from src.conversation.conversation_policy import ConversationPolicy
from src.interaction.events import PresenceEvent, PresenceEventType


def test_conversation_policy_rules():
    policy = ConversationPolicy()
    event = PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="Face_1",
        name="Sarah",
        relationship="Daughter",
    )

    # 1. Safety Override
    state, strat = policy.evaluate_policy(
        event, SpeakerRole.PATIENT, ConversationState.IDLE, assistance_level=5
    )
    assert state == ConversationState.RESPONDING
    assert strat == ResponseStrategy.SAFETY_ALERT

    # 2. Initial Encounter Greeting
    state, strat = policy.evaluate_policy(
        event, SpeakerRole.VISITOR, ConversationState.IDLE, assistance_level=0
    )
    assert state == ConversationState.GREETING
    assert strat == ResponseStrategy.GREETING

    # 3. Patient Speaking -> Supportive Silence
    state, strat = policy.evaluate_policy(
        event, SpeakerRole.PATIENT, ConversationState.LISTENING, assistance_level=0
    )
    assert state == ConversationState.PATIENT_SPEAKING
    assert strat == ResponseStrategy.SUPPORTIVE_SILENCE
