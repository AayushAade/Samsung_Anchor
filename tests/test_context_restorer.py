"""
Unit tests for the Context Restorer.
"""

from src.cognition.context_cue import CueType
from src.cognition.context_restorer import ContextRestorer


def test_unknown_identity():

    restorer = ContextRestorer()

    cue = restorer.restore_identity(None)

    assert cue.cue_type == CueType.IDENTITY
    assert cue.text == "Unknown person."
    assert cue.priority == 5


def test_identity_with_name():

    restorer = ContextRestorer()

    cue = restorer.restore_identity(
        {
            "display_name": "Sid",
            "relationship": None,
            "confidence": 0.90,
        }
    )

    assert cue.cue_type == CueType.IDENTITY
    assert cue.text == "Sid."
    assert cue.priority == 10
    assert cue.confidence == 0.90


def test_identity_with_relationship():

    restorer = ContextRestorer()

    cue = restorer.restore_identity(
        {
            "display_name": "Sid",
            "relationship": "Grandson",
            "confidence": 0.95,
        }
    )

    assert cue.cue_type == CueType.IDENTITY
    assert cue.text == "Sid. Grandson."
    assert cue.priority == 10
    assert cue.confidence == 0.95


def test_missing_name():

    restorer = ContextRestorer()

    cue = restorer.restore_identity(
        {
            "display_name": None,
            "relationship": "Brother",
        }
    )

    assert cue.text == "Unknown person."