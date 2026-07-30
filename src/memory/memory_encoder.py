"""
MEMORA Memory Encoder.

Converts heterogeneous cognitive payloads (observations, experiences, knowledge facts, executive outcomes)
into unified, standardized MemoryRecord objects.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.memory.memory_models import MemoryCategory, MemoryRecord, RetentionPolicy


class MemoryEncoder:
    """
    Standardized memory record encoder.
    """

    @classmethod
    def encode_observation(
        cls,
        content: str,
        origin: str = "PerceptionManager",
        importance: float = 0.50,
        related_entities: Optional[List[str]] = None,
        context_snapshot: Optional[Dict[str, Any]] = None,
    ) -> MemoryRecord:
        return MemoryRecord(
            content=content,
            category=MemoryCategory.OBSERVATION,
            origin=origin,
            importance=importance,
            retention_policy=RetentionPolicy.TEMPORARY,
            related_entities=related_entities or [],
            context_snapshot=context_snapshot or {},
        )

    @classmethod
    def encode_experience(
        cls,
        content: str,
        origin: str = "ExperienceEngine",
        importance: float = 0.75,
        related_experiences: Optional[List[str]] = None,
    ) -> MemoryRecord:
        return MemoryRecord(
            content=content,
            category=MemoryCategory.EXPERIENCE,
            origin=origin,
            importance=importance,
            retention_policy=RetentionPolicy.CLINICAL,
            related_experiences=related_experiences or [],
        )

    @classmethod
    def encode_knowledge_fact(
        cls,
        content: str,
        origin: str = "KnowledgeEngine",
        importance: float = 0.90,
        knowledge_references: Optional[List[str]] = None,
    ) -> MemoryRecord:
        return MemoryRecord(
            content=content,
            category=MemoryCategory.KNOWLEDGE_FACT,
            origin=origin,
            importance=importance,
            retention_policy=RetentionPolicy.CLINICAL,
            knowledge_references=knowledge_references or [],
        )
