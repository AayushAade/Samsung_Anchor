"""
MEMORA Memory Consolidator.

Deduplicates and merges related memory records, updates importance weights,
and increments version history without overwriting historical records.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from src.memory.memory_models import MemoryRecord
from src.memory.memory_repository import MemoryRepository


class MemoryConsolidator:
    """
    Deterministic memory consolidation and deduplication engine.
    """

    def __init__(self, repository: MemoryRepository) -> None:
        self.repository = repository

    def consolidate_new_record(self, record: MemoryRecord) -> Tuple[MemoryRecord, bool]:
        """
        Consolidate a new memory record against active repository memories.
        Returns (consolidated_record, is_duplicate_merged).
        """
        active = self.repository.get_all_active()
        rec_lower = record.content.lower()

        for existing in active:
            if existing.content.lower() == rec_lower and existing.category == record.category:
                # Merge into existing memory record: update importance, merge entities, increment version
                existing.importance = round(max(existing.importance, record.importance) + 0.05, 3)
                existing.version += 1
                for ent in record.related_entities:
                    if ent not in existing.related_entities:
                        existing.related_entities.append(ent)
                return (existing, True)

        # No duplicate found; add new record to repository
        self.repository.add_record(record)
        return (record, False)
