from src.cognition.memory_models import (
    MemoryType,
    RelevantMemory,
)

from src.interaction.actions import InteractionActionType
from src.pipeline.cognitive_pipeline import CognitivePipeline


def test_person_arrival_generates_action():

    pipeline = CognitivePipeline()

    result = {
        "face_id": "1",
        "name": "Alice",
        "relationship": "Friend",
    }

    actions = pipeline.process(result)

    assert len(actions) == 1
    assert actions[0].type == InteractionActionType.SPEAK


def test_memory_is_recalled():

    pipeline = CognitivePipeline()

    pipeline.memory_repository.save(
        RelevantMemory(
            memory_id="1",
            memory_type=MemoryType.EPISODIC,
            person="Alice",
            summary="discussed Samsung Anchor.",
        )
    )

    result = {
        "face_id": "1",
        "name": "Alice",
        "relationship": "Friend",
    }

    actions = pipeline.process(result)

    assert len(actions) == 1

    assert (
        "Last time you discussed Samsung Anchor."
        in actions[0].message
    )


def test_same_person_not_announced_twice():

    pipeline = CognitivePipeline()

    result = {
        "face_id": "1",
        "name": "Alice",
        "relationship": "Friend",
    }

    pipeline.process(result)

    actions = pipeline.process(result)

    assert actions == []


def test_reset_allows_new_greeting():

    pipeline = CognitivePipeline()

    result = {
        "face_id": "1",
        "name": "Alice",
        "relationship": "Friend",
    }

    pipeline.process(result)

    pipeline.reset()

    actions = pipeline.process(result)

    assert len(actions) == 1