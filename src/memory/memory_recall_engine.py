"""
MEMORA Cognitive Memory Recall Engine.

Executes deterministic memory recall queries:
- Exact ID & content recall
- Entity & Location recall
- Temporal & Category recall
Generates step-by-step recall explanation narratives.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from src.memory.memory_index import MemoryIndex
from src.memory.memory_models import MemoryCategory, MemoryRecord
from src.memory.memory_repository import MemoryRepository


class MemoryRecallEngine:
    """
    Deterministic memory recall engine.
    """

    def __init__(self, repository: MemoryRepository, index: MemoryIndex) -> None:
        self.repository = repository
        self.index = index

    def recall_by_keyword(self, keyword: str, limit: int = 5) -> Tuple[List[MemoryRecord], str]:
        """
        Recall memories matching a keyword, sorted by importance.
        Returns (recalled_memories, explanation_narrative).
        """
        kw_lower = keyword.lower()
        active = self.repository.get_all_active()
        matched = [m for m in active if kw_lower in m.content.lower() or any(kw_lower in e.lower() for e in m.related_entities)]

        matched.sort(key=lambda m: m.importance, reverse=True)
        results = matched[:limit]

        explanation = (
            f"Deterministic Recall for keyword '{keyword}': "
            f"Evaluated {len(active)} active memories, found {len(matched)} matches. "
            f"Returning top {len(results)} by importance weight."
        )

        return results, explanation
