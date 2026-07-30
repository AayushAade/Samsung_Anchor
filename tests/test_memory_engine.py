from src.cognition.memory_engine import MemoryEngine
from src.cognition.memory_models import (
    RelevantMemory,
    MemoryType,
)
from src.cognition.memory_query import MemoryQuery
from src.cognition.memory_repository import MemoryRepository


def test_engine_retrieves_repository_results():

    repository = MemoryRepository()

    repository.save(
        RelevantMemory(
            memory_id="1",
            memory_type=MemoryType.EPISODIC,
            person="Alice",
            title="Samsung Prototype",
        )
    )

    engine = MemoryEngine(repository)

    results = engine.retrieve(
        MemoryQuery(face_id="Alice")
    )

    assert len(results) == 1
    assert results[0].title == "Samsung Prototype"


def test_engine_returns_empty():

    repository = MemoryRepository()

    engine = MemoryEngine(repository)

    assert engine.retrieve(
        MemoryQuery(face_id="Alice")
    ) == []