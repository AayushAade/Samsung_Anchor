"""
MEMORA Multi-Index Registry.

Provides synchronized multi-indexing over MemoryRepository:
- Chronological index
- Entity index
- Location index
- Importance index
- Category index
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from src.memory.memory_models import MemoryCategory, MemoryRecord
from src.memory.memory_repository import MemoryRepository


class MemoryIndex:
    """
    Multi-index registry synchronizing queries over MemoryRepository.
    """

    def __init__(self, repository: MemoryRepository) -> None:
        self.repository = repository

    def query_by_entity(self, entity_name: str) -> List[MemoryRecord]:
        ent_lower = entity_name.lower()
        active = self.repository.get_all_active()
        return [
            m for m in active
            if any(ent_lower in e.lower() for e in m.related_entities)
            or ent_lower in m.content.lower()
        ]

    def query_by_category(self, category: MemoryCategory) -> List[MemoryRecord]:
        active = self.repository.get_all_active()
        return [m for m in active if m.category == category]

    def query_by_importance(self, min_importance: float = 0.80) -> List[MemoryRecord]:
        active = self.repository.get_all_active()
        return [m for m in active if m.importance >= min_importance]
