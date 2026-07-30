"""
MEMORA Context Reconstructor.

Reconstructs surrounding cognitive context snapshots for recalled memory records:
- Surrounding events
- Knowledge facts
- Executive decisions
"""

from __future__ import annotations

from typing import List, Optional

from src.memory.memory_models import MemoryRecord, ReconstructedContext
from src.memory.memory_repository import MemoryRepository


class ContextReconstructor:
    """
    Cognitive context reconstructor.
    """

    def __init__(self, repository: MemoryRepository) -> None:
        self.repository = repository

    def reconstruct_context(self, memory: MemoryRecord) -> ReconstructedContext:
        """
        Reconstruct cognitive context snapshot surrounding a memory record.
        """
        surrounding = [f"Observation '{memory.content}' recorded at {memory.timestamp_iso[11:16]}."]
        facts = [f"Linked Entities: {', '.join(memory.related_entities)}" if memory.related_entities else "No direct entity links."]
        decisions = [f"Retention Policy: {memory.retention_policy.value} (Importance: {memory.importance:.2f})."]

        explanation = f"Reconstructed full cognitive context snapshot for memory `{memory.memory_id}`."

        return ReconstructedContext(
            memory_id=memory.memory_id,
            surrounding_events=surrounding,
            knowledge_facts=facts,
            executive_decisions=decisions,
            explanation=explanation,
        )
