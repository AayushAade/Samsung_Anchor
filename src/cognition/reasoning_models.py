from __future__ import annotations

from dataclasses import dataclass

from src.cognition.memory_models import RelevantMemory


@dataclass(frozen=True)
class MemoryRecall:
    """
    Represents the memories that should be surfaced to the user
    for the current situation.
    """

    should_greet: bool = True

    recalled_memories: list[RelevantMemory] | None = None