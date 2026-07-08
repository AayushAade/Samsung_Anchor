from src.cognition.memory_models import (
    RelevantMemory,
    MemoryImportance,
    MemoryType,
)


def test_memory_defaults():

    memory = RelevantMemory(
        memory_id="mem001",
        memory_type=MemoryType.EPISODIC,
    )

    assert memory.importance == MemoryImportance.NORMAL
    assert memory.commitments == []
    assert memory.tags == []


def test_memory_fields():

    memory = RelevantMemory(
        memory_id="mem002",
        memory_type=MemoryType.SEMANTIC,
        title="Alice",
        summary="Teammate",
    )

    assert memory.title == "Alice"
    assert memory.summary == "Teammate"