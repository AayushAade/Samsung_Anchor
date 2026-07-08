from __future__ import annotations

from src.cognition.memory_models import RelevantMemory
from src.cognition.reasoning_models import MemoryRecall


class ReasoningEngine:
    """
    Determines which retrieved memories should be surfaced.
    """

    def recall(
        self,
        memories: list[RelevantMemory],
    ) -> MemoryRecall:

        if not memories:
            return MemoryRecall(
                should_greet=True,
                recalled_memories=[],
            )

        return MemoryRecall(
            should_greet=True,
            recalled_memories=memories[:1],
        )