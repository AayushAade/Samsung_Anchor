"""
Unit tests for CueManager.
"""

from src.cognition.context_cue import (
    ContextCue,
    CueType,
)

from src.cognition.cue_manager import CueManager


def test_empty_queue():

    manager = CueManager()

    assert manager.next() is None


def test_single_cue():

    manager = CueManager()

    cue = ContextCue(
        cue_type=CueType.IDENTITY,
        text="Sid.",
        priority=10,
    )

    manager.add(cue)

    assert manager.next() == cue
    assert manager.next() is None


def test_priority_order():

    manager = CueManager()

    low = ContextCue(
        cue_type=CueType.OBJECT,
        text="Keys.",
        priority=1,
    )

    high = ContextCue(
        cue_type=CueType.REMINDER,
        text="Medicine.",
        priority=100,
    )

    medium = ContextCue(
        cue_type=CueType.IDENTITY,
        text="Sid.",
        priority=10,
    )

    manager.add(low)
    manager.add(high)
    manager.add(medium)

    assert manager.next() == high
    assert manager.next() == medium
    assert manager.next() == low


def test_clear():

    manager = CueManager()

    manager.add(
        ContextCue(
            cue_type=CueType.IDENTITY,
            text="Sid.",
        )
    )

    manager.clear()

    assert manager.next() is None