"""
Unit tests for CueFormatter.
"""

from src.cognition.context_cue import (
    ContextCue,
    CueType,
)
from src.cognition.cue_formatter import CueFormatter


def test_identity_format():

    formatter = CueFormatter()

    cue = ContextCue(
        cue_type=CueType.IDENTITY,
        text="Sid. Grandson.",
    )

    assert formatter.format(cue) == "Sid. Grandson."


def test_object_format():

    formatter = CueFormatter()

    cue = ContextCue(
        cue_type=CueType.OBJECT,
        text="Keys. Study table.",
    )

    assert formatter.format(cue) == "Keys. Study table."


def test_empty_spaces_removed():

    formatter = CueFormatter()

    cue = ContextCue(
        cue_type=CueType.IDENTITY,
        text="   Sid.   ",
    )

    assert formatter.format(cue) == "Sid."