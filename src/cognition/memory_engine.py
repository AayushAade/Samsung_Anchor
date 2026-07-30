"""
Memory Engine.

Retrieves memories relevant to the current situation.
"""

from __future__ import annotations

from src.cognition.memory_models import RelevantMemory
from src.cognition.memory_query import MemoryQuery
from src.cognition.memory_repository import MemoryRepository


class MemoryEngine:
    """
    Cognitive retrieval engine.

    The engine performs retrieval logic.
    Storage is delegated to the repository.
    """

    def __init__(
        self,
        repository: MemoryRepository,
    ) -> None:

        self.repository = repository

    def retrieve(
        self,
        query: MemoryQuery,
    ) -> list[RelevantMemory]:
        """
        Retrieve memories relevant to the current situation.
        """

        return self.repository.find(query)