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