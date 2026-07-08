from src.cognition.memory_models import (
    MemoryType,
    RelevantMemory,
)
from src.cognition.reasoning_models import MemoryRecall
from src.interaction.actions import InteractionActionType
from src.interaction.events import (
    PresenceEvent,
    PresenceEventType,
)
from src.interaction.interaction_manager import (
    InteractionManager,
)


def create_event():

    return PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="1",
        name="Alice",
        relationship="Friend",
    )


def test_person_arrived():

    manager = InteractionManager()

    action = manager.handle_event(create_event())

    assert action is not None
    assert action.type == InteractionActionType.SPEAK
    assert action.message == (
        "Alice is here. They are your Friend."
    )


def test_person_with_memory():

    manager = InteractionManager()

    recall = MemoryRecall(
        recalled_memories=[
            RelevantMemory(
                memory_id="1",
                memory_type=MemoryType.EPISODIC,
                summary="discussed the Samsung prototype.",
            )
        ]
    )

    action = manager.handle_event(
        create_event(),
        recall,
    )

    assert (
        "Last time you discussed the Samsung prototype."
        in action.message
    )


def test_person_with_commitment():

    manager = InteractionManager()

    recall = MemoryRecall(
        recalled_memories=[
            RelevantMemory(
                memory_id="1",
                memory_type=MemoryType.EPISODIC,
                summary="discussed the Samsung prototype.",
                commitments=[
                    "send the presentation"
                ],
            )
        ]
    )

    action = manager.handle_event(
        create_event(),
        recall,
    )

    assert (
        "You also planned to send the presentation."
        in action.message
    )


def test_unknown_person():

    manager = InteractionManager()

    event = PresenceEvent(
        type=PresenceEventType.UNKNOWN_PERSON_DETECTED,
        face_id="42",
        name=None,
    )

    assert manager.handle_event(event) is None