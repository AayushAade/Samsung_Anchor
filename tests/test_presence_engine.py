from src.interaction.presence_engine import PresenceEngine


def test_greet_known_person():

    engine = PresenceEngine()

    greeting = engine.process(
        {
            "face_id": "1",
            "name": "Alice",
            "relationship": "Friend",
        }
    )

    assert greeting == "Alice is here. They are your Friend."


def test_same_person_only_once():

    engine = PresenceEngine()

    result = {
        "face_id": "1",
        "name": "Alice",
        "relationship": "Friend",
    }

    assert engine.process(result) is not None
    assert engine.process(result) is None


def test_unknown_person():

    engine = PresenceEngine()

    greeting = engine.process(
        {
            "face_id": "1",
            "name": None,
            "relationship": None,
        }
    )

    assert greeting is None


def test_different_people():

    engine = PresenceEngine()

    first = engine.process(
        {
            "face_id": "1",
            "name": "Alice",
            "relationship": "Friend",
        }
    )

    second = engine.process(
        {
            "face_id": "2",
            "name": "Bob",
            "relationship": "Brother",
        }
    )

    assert first is not None
    assert second is not None


def test_reset():

    engine = PresenceEngine()

    result = {
        "face_id": "1",
        "name": "Alice",
        "relationship": "Friend",
    }

    engine.process(result)

    engine.reset()

    assert engine.process(result) is not None