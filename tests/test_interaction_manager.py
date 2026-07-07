from src.interaction.actions import InteractionActionType
from src.interaction.events import (
    PresenceEvent,
    PresenceEventType,
)
from src.interaction.interaction_manager import (
    InteractionManager,
)


def test_person_arrived():

    manager = InteractionManager()

    event = PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="1",
        name="Alice",
        relationship="Friend",
    )

    action = manager.handle_event(event)

    assert action is not None
    assert action.type == InteractionActionType.SPEAK
    assert action.message == (
        "Alice is here. They are your Friend."
    )


def test_person_without_relationship():

    manager = InteractionManager()

    event = PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="1",
        name="Alice",
        relationship=None,
    )

    action = manager.handle_event(event)

    assert action is not None
    assert action.message == "Alice is here."


def test_unknown_person():

    manager = InteractionManager()

    event = PresenceEvent(
        type=PresenceEventType.UNKNOWN_PERSON_DETECTED,
        face_id="42",
        name=None,
    )

    action = manager.handle_event(event)

    assert action is None