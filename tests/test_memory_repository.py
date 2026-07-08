from src.cognition.memory_models import (
    RelevantMemory,
    MemoryType,
)
from src.cognition.memory_query import MemoryQuery
from src.cognition.memory_repository import MemoryRepository


def test_save_and_find():

    repository = MemoryRepository()

    memory = RelevantMemory(
        memory_id="mem001",
        memory_type=MemoryType.EPISODIC,
        person="Alice",
        title="Samsung",
    )

    repository.save(memory)

    results = repository.find(
        MemoryQuery(face_id="Alice")
    )

    assert len(results) == 1
    assert results[0].title == "Samsung"


def test_unknown_person():

    repository = MemoryRepository()

    results = repository.find(
        MemoryQuery(face_id="Bob")
    )

    assert results == []


def test_clear():

    repository = MemoryRepository()

    repository.save(
        RelevantMemory(
            memory_id="1",
            memory_type=MemoryType.EPISODIC,
            person="Alice",
        )
    )

    repository.clear()

    assert repository.find(
        MemoryQuery(face_id="Alice")
    ) == []