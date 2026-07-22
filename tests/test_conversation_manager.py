from src.conversation.conversation_manager import ConversationManager
from src.conversation.conversation_models import ConversationState, ResponseStrategy, SpeakerRole
from src.interaction.events import PresenceEvent, PresenceEventType


def test_conversation_manager_initialization():
    manager = ConversationManager()
    assert manager.dialogue_tracker.state == ConversationState.IDLE
    assert manager.turn_manager.get_active_speaker() == SpeakerRole.PATIENT


def test_conversation_manager_process_cycle():
    manager = ConversationManager()
    event = PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="Face_1",
        name="Sarah",
        relationship="Daughter",
    )

    ctx = manager.process_cycle(event)

    assert ctx is not None
    assert ctx.turn_count == 1
    assert ctx.state in [ConversationState.GREETING, ConversationState.RESPONDING, ConversationState.PATIENT_SPEAKING, ConversationState.SILENT_OBSERVATION]
    assert ctx.response_strategy is not None


def test_conversation_manager_reset():
    manager = ConversationManager()
    event = PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="Face_1",
        name="Sarah",
        relationship="Daughter",
    )

    manager.process_cycle(event)
    manager.reset()

    assert manager.dialogue_tracker.state == ConversationState.IDLE
    assert manager.dialogue_tracker.turn_count == 0
