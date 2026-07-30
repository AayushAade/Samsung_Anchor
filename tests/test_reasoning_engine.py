from src.cognition.memory_models import (
    RelevantMemory,
    MemoryType,
)
from src.cognition.reasoning_engine import ReasoningEngine


def test_empty_recall():

    engine = ReasoningEngine()

    result = engine.recall([])

    assert result.should_greet is True
    assert result.recalled_memories == []


def test_recall_first_memory():

    engine = ReasoningEngine()

    memories = [
        RelevantMemory(
            memory_id="1",
            memory_type=MemoryType.EPISODIC,
            title="Samsung",
        ),
        RelevantMemory(
            memory_id="2",
            memory_type=MemoryType.EPISODIC,
            title="Hackathon",
        ),
    ]

    result = engine.recall(memories)

    assert len(result.recalled_memories) == 1
    assert result.recalled_memories[0].title == "Samsung"