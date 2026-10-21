"""
Unit tests for the Identity Learning Pipeline.

These tests verify that the orchestration layer correctly coordinates
the Reasoning and Memory subsystems without depending on SQLite,
Gemini, or the microphone.
"""

from src.integration.identity_learning_pipeline import process_identity_learning


class FakeBinder:
    """Fake Context Binder used for testing."""

    def __init__(self, response):
        self.response = response

    def parse_transcript(self, transcript):
        return self.response


class FakeDatabase:
    """Fake Memory Database used for testing."""

    def __init__(self, response):
        self.response = response
        self.calls = []

    def add_evidence(
        self,
        identity_id,
        name,
        relationship=None,
        raw_transcript=None,
    ):
        self.calls.append(
            {
                "identity_id": identity_id,
                "name": name,
                "relationship": relationship,
                "raw_transcript": raw_transcript,
            }
        )
        return self.response


def test_missing_face_id():
    binder = FakeBinder({})
    database = FakeDatabase({})

    result = process_identity_learning(
        "",
        "Hello",
        database,
        binder,
    )

    assert result["success"] is False
    assert result["reason"] == "Missing face_id"


def test_empty_transcript():
    binder = FakeBinder({})
    database = FakeDatabase({})

    result = process_identity_learning(
        "Anonymous_ID_1",
        "",
        database,
        binder,
    )

    assert result["success"] is False
    assert result["reason"] == "Empty transcript"


def test_no_name_extracted():
    binder = FakeBinder(
        {
            "name": None,
            "relationship": None,
        }
    )

    database = FakeDatabase({})

    result = process_identity_learning(
        "Anonymous_ID_1",
        "Hello there",
        database,
        binder,
    )

    assert result["success"] is False
    assert result["reason"] == "No identity information extracted"


def test_successful_learning_with_name_key():
    """Backward compatibility with 'name' key."""

    binder = FakeBinder(
        {
            "name": "Rahul",
            "relationship": "Brother",
        }
    )

    database = FakeDatabase(
        {
            "name": "Rahul",
            "relationship": "Brother",
            "confidence": 0.90,
            "is_confirmed": True,
        }
    )

    result = process_identity_learning(
        "Anonymous_ID_1",
        "This is my brother Rahul.",
        database,
        binder,
    )

    assert result["success"] is True
    assert result["identity_id"] == "Anonymous_ID_1"
    assert result["name"] == "Rahul"
    assert result["relationship"] == "Brother"
    assert result["confidence"] == 0.90
    assert result["is_confirmed"] is True

    assert len(database.calls) == 1
    assert database.calls[0]["identity_id"] == "Anonymous_ID_1"
    assert database.calls[0]["name"] == "Rahul"


def test_successful_learning_with_extracted_name_key():
    """Current production Context Binder API."""

    binder = FakeBinder(
        {
            "extracted_name": "Rahul",
            "relationship": "Brother",
        }
    )

    database = FakeDatabase(
        {
            "name": "Rahul",
            "relationship": "Brother",
            "confidence": 0.90,
            "is_confirmed": True,
        }
    )

    result = process_identity_learning(
        "Anonymous_ID_1",
        "This is my brother Rahul.",
        database,
        binder,
    )

    assert result["success"] is True
    assert result["identity_id"] == "Anonymous_ID_1"
    assert result["name"] == "Rahul"
    assert result["relationship"] == "Brother"
    assert result["confidence"] == 0.90
    assert result["is_confirmed"] is True


def test_invalid_parser_response():
    binder = FakeBinder("Invalid Response")
    database = FakeDatabase({})

    result = process_identity_learning(
        "Anonymous_ID_1",
        "Hello",
        database,
        binder,
    )

    assert result["success"] is False
    assert result["reason"] == "Invalid parser response"

def _consenting_db(tmp_path):
    import numpy as np
    from src.memory.database import MemoraDatabase
    db = MemoraDatabase(str(tmp_path / "id.sqlite"))
    for feature in ("CONVERSATION_STORAGE", "FACE_RECOGNITION"):
        db._set_system_state(f"consent:{feature}", "granted@2026-10-21T00:00:00")
    return db, db.register_anonymous(np.ones(128, dtype=np.float32) / np.sqrt(128))


def test_confirmed_identity_is_not_renamed_and_conflict_is_reported(tmp_path):
    from src.reasoning.context_binder import MemoraContextBinder
    db, face = _consenting_db(tmp_path)
    binder = MemoraContextBinder()
    assert process_identity_learning(face, "Hi, I'm Bob, your son.", db, binder)["success"] is True
    result = process_identity_learning(face, "I'm Tom, your neighbour.", db, binder)
    assert result["success"] is False and result["reason"] == "Name conflict"
    assert result["name"] == "Bob" and result["heard_name"] == "Tom"
    assert process_identity_learning(face, "I'm Bob.", db, binder)["success"] is True


def test_conflicting_introduction_creates_no_episode_under_the_confirmed_name(tmp_path):
    """Found in review: Tom's words were saved as an episode with Bob."""
    import threading
    from src.integration.async_identity_learning import start_identity_learning
    from src.reasoning.context_binder import MemoraContextBinder
    db, face = _consenting_db(tmp_path)
    binder = MemoraContextBinder()
    process_identity_learning(face, "Hi, I'm Bob, your son.", db, binder)

    class Listener:
        def listen_and_transcribe(self):
            return "I'm Tom, your neighbour."

    class MemoryManager:
        def process_episode(self, episode):
            raise AssertionError("no episode should be consolidated")

    done, results = threading.Event(), []
    start_identity_learning(face_id=face, listener=Listener(), binder=binder, database=db,
                            memory_manager=MemoryManager(), speaker=None,
                            on_finished=lambda f, r: (results.append(r), done.set()))
    assert done.wait(10)
    assert results[0]["reason"] == "Name conflict"
    assert db.episode_repo.count() == 0


def test_identity_learning_stores_no_inferred_knowledge_by_default(tmp_path):
    """The memory consolidator only stores facts a language model extracts; with the
    default (mock) client nothing is inferred, so no 'semantic' knowledge can be presented
    as something the person said. Guard against that changing silently."""
    import sqlite3
    import threading
    import time
    from src.cognition.cognitive_memory_manager import CognitiveMemoryManager
    from src.integration.async_identity_learning import start_identity_learning
    from src.llm.reasoning_client import MockReasoningClient
    from src.reasoning.context_binder import MemoraContextBinder
    db, face = _consenting_db(tmp_path)
    manager = CognitiveMemoryManager(db.SessionFactory, MockReasoningClient())

    class Listener:
        def listen_and_transcribe(self):
            return "Hi, I'm Bob, your son. I love fishing on Sundays."

    done = threading.Event()
    start_identity_learning(face_id=face, listener=Listener(), binder=MemoraContextBinder(), database=db,
                            memory_manager=manager, speaker=None, on_finished=lambda f, r: done.set())
    assert done.wait(10)
    manager.executor.shutdown(wait=True)
    time.sleep(0.05)
    con = sqlite3.connect(db.db_path)
    try:
        assert con.execute("select count(*) from semantic_nodes").fetchone()[0] == 0
        assert con.execute("select count(*) from episodes").fetchone()[0] == 1
    finally:
        con.close()
