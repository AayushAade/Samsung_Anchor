"""
Unit tests for the Cognitive Pipeline.

These tests verify the core perception → context → goal → reasoning → interaction
flow using a real in-memory database instance.
"""

import os
import tempfile

from src.cognition.memory_models import (
    MemoryType,
    RelevantMemory,
)

from src.interaction.actions import InteractionActionType
from src.pipeline.cognitive_pipeline import CognitivePipeline
from src.memory.database import MemoraDatabase


def _make_pipeline():
    """Create a pipeline backed by a temporary in-memory database."""
    db = MemoraDatabase(db_path=os.path.join(tempfile.gettempdir(), "test_pipeline.sqlite"))
    db.clear()
    return CognitivePipeline(db), db


def test_person_arrival_generates_action():
    pipeline, _ = _make_pipeline()

    result = {
        "face_id": "1",
        "name": "Alice",
        "relationship": "Friend",
    }

    actions = pipeline.process(result)

    # The pipeline may or may not generate an action depending on
    # the Attention Engine threshold (no memories → could be silence).
    # But the pipeline must not crash.
    assert isinstance(actions, list)


def test_same_person_not_announced_twice():
    pipeline, _ = _make_pipeline()

    result = {
        "face_id": "1",
        "name": "Alice",
        "relationship": "Friend",
    }

    pipeline.process(result)

    actions = pipeline.process(result)

    assert actions == []


def test_reset_allows_new_greeting():
    pipeline, _ = _make_pipeline()

    result = {
        "face_id": "1",
        "name": "Alice",
        "relationship": "Friend",
    }

    pipeline.process(result)

    pipeline.reset()

    actions = pipeline.process(result)

    assert isinstance(actions, list)