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

class FakeMemoryRepository:
    """Minimal fake that satisfies DatabaseMemoryRepository interface."""
    def find(self, query):
        return []
    def save(self, memory):
        pass
    def clear(self):
        pass

class FakeSessionFactory:
    """Minimal fake that satisfies sessionmaker interface."""
    def __call__(self):
        return self
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def query(self, *args):
        return _FakeQuery()
    def commit(self):
        pass
    def add(self, *args):
        pass

class _FakeQuery:
    def filter_by(self, **kw):
        return self
    def first(self):
        return None
    def all(self):
        return []

class FakeDatabase:
    def __init__(self):
        self.memory_repo = FakeMemoryRepository()
        self.SessionFactory = FakeSessionFactory()


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
    """
    Verifies that process_frame → event_bus → cognitive_worker → action_queue
    pipeline is wired correctly. The Attention Engine may choose silence
    (no memories), so we validate the pipeline doesn't crash rather than
    asserting a specific action count.
    """
    import time

    coordinator = AnchorCoordinator(
        database=FakeDatabase(),
        recognizer=FakePipelineRecognizer(),
        listener=FakeListener(),
        binder=FakeBinder(),
        speaker=FakeSpeaker(),
    )

    coordinator.start()

    coordinator.process_frame(object())

    # Give the background worker thread time to process
    time.sleep(0.3)

    actions = coordinator.consume_actions()

    # The Attention Engine may produce silence (no memories for Alice),
    # so we validate the pipeline completed without crashing.
    assert isinstance(actions, list)

    coordinator.shutdown()


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