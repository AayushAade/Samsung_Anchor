"""
Memory Repository.

Persistence layer for Anchor's long-term memories.

The repository is responsible only for storing and retrieving
RelevantMemory objects. It does not perform ranking or reasoning.
"""

from __future__ import annotations

from src.cognition.memory_models import RelevantMemory
from src.cognition.memory_query import MemoryQuery


class MemoryRepository:
    """
    In-memory implementation of the memory repository.

    This implementation is intentionally simple.
    A future version will use SQLite or a vector database.
    """

    def __init__(self) -> None:
        self._memories: list[RelevantMemory] = []

    def save(
        self,
        memory: RelevantMemory,
    ) -> None:
        """
        Store a memory.
        """

        self._memories.append(memory)

    def find(
        self,
        query: MemoryQuery,
    ) -> list[RelevantMemory]:
        """
        Retrieve candidate memories.

        Current strategy:
        - Match memories by person.
        """

        results: list[RelevantMemory] = []

        for memory in self._memories:

            if (
                query.face_id is not None
                and memory.person == query.face_id
            ):
                results.append(memory)

        return results

    def clear(self) -> None:
        """
        Remove all stored memories.
        """

        self._memories.clear()