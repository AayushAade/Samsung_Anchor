"""
Unit tests for the Anchor Coordinator.

These tests verify that the coordinator correctly orchestrates
the various subsystems without testing their internal logic.
"""

from unittest.mock import patch

from src.coordinator.anchor_coordinator import AnchorCoordinator


# ==========================================================
# Fake Subsystems
# ==========================================================

class FakeDatabase:
    pass


class FakeRecognizer:
    def __init__(self):
        self.called = False

    def process_frame(self, frame, database):
        self.called = True
        return {
            "frame": frame,
            "database": database,
        }


class FakePipelineRecognizer:
    def process_frame(self, frame, database):
        return [
            {
                "face_id": "1",
                "name": "Alice",
                "relationship": "Friend",
            }
        ]


class FakeListener:
    pass


class FakeBinder:
    pass


class FakeSpeaker:
    pass


# ==========================================================
# Coordinator Factory
# ==========================================================

def create_coordinator():
    return AnchorCoordinator(
        database=FakeDatabase(),
        recognizer=FakeRecognizer(),
        listener=FakeListener(),
        binder=FakeBinder(),
        speaker=FakeSpeaker(),
    )


# ==========================================================
# Tests
# ==========================================================

def test_initialize():
    coordinator = create_coordinator()

    coordinator.running = True

    coordinator.initialize()

    assert coordinator.running is False
    assert coordinator.consume_actions() == []


def test_start():
    coordinator = create_coordinator()

    coordinator.start()

    assert coordinator.running is True


def test_shutdown():
    coordinator = create_coordinator()

    coordinator.start()
    coordinator.shutdown()

    assert coordinator.running is False


def test_process_frame():
    coordinator = create_coordinator()

    frame = object()

    result = coordinator.process_frame(frame)

    assert coordinator.recognizer.called is True
    assert result["frame"] is frame
    assert result["database"] is coordinator.database


def test_consume_actions_empty():
    coordinator = create_coordinator()

    assert coordinator.consume_actions() == []


def test_pending_actions_generated():

    coordinator = AnchorCoordinator(
        database=FakeDatabase(),
        recognizer=FakePipelineRecognizer(),
        listener=FakeListener(),
        binder=FakeBinder(),
        speaker=FakeSpeaker(),
    )

    coordinator.process_frame(object())

    actions = coordinator.consume_actions()

    assert len(actions) == 1
    assert actions[0].message == (
        "Alice is here. They are your Friend."
    )

    assert coordinator.consume_actions() == []


@patch("src.coordinator.anchor_coordinator.process_identity_learning")
def test_process_transcript(mock_pipeline):
    mock_pipeline.return_value = {
        "success": True,
        "identity_id": "Anonymous_ID_1",
    }

    coordinator = create_coordinator()

    result = coordinator.process_transcript(
        "Anonymous_ID_1",
        "Hello",
    )

    mock_pipeline.assert_called_once_with(
        face_id="Anonymous_ID_1",
        transcript="Hello",
        database=coordinator.database,
        binder=coordinator.binder,
    )

    assert result["success"] is True
    assert result["identity_id"] == "Anonymous_ID_1"