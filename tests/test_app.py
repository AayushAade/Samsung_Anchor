"""
Unit tests for the Samsung Anchor application bootstrap.

These tests verify that the application constructs the
AnchorCoordinator correctly without depending on the real
Vision, Audio, Memory, or Reasoning implementations.
"""

from unittest.mock import patch

from app import build_application, main


# ==========================================================
# Fake Subsystems
# ==========================================================

class FakeDatabase:
    pass


class FakeRecognizer:
    pass


class FakeListener:
    pass


class FakeBinder:
    pass


class FakeSpeaker:
    pass


# ==========================================================
# Tests
# ==========================================================

def test_build_application():
    database = FakeDatabase()
    recognizer = FakeRecognizer()
    listener = FakeListener()
    binder = FakeBinder()
    speaker = FakeSpeaker()

    coordinator = build_application(
        database=database,
        recognizer=recognizer,
        listener=listener,
        binder=binder,
        speaker=speaker,
    )

    assert coordinator.database is database
    assert coordinator.recognizer is recognizer
    assert coordinator.listener is listener
    assert coordinator.binder is binder
    assert coordinator.speaker is speaker


@patch("builtins.print")
def test_main(mock_print):
    main()

    mock_print.assert_any_call("Samsung Anchor")
    mock_print.assert_any_call("Application bootstrap initialized.")