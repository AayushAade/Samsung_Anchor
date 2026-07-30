"""
MEMORA Long-Term Memory Consolidation Data Models.

Provides value objects for:
- Retention Policies & Memory Categories
- Unified MemoryRecords with provenance tracking
- Reconstructed Context Payloads
- Memory Summary Payloads
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class RetentionPolicy(str, Enum):
    CLINICAL = "CLINICAL"          # Never expire
    TEMPORARY = "TEMPORARY"        # Expire in 30 days
    DIAGNOSTIC = "DIAGNOSTIC"      # Expire in 7 days


class MemoryCategory(str, Enum):
    OBSERVATION = "OBSERVATION"
    EXPERIENCE = "EXPERIENCE"
    KNOWLEDGE_FACT = "KNOWLEDGE_FACT"
    EXECUTIVE_OUTCOME = "EXECUTIVE_OUTCOME"
    CONVERSATION = "CONVERSATION"


@dataclass
class MemoryRecord:
    """
    Unified long-term cognitive memory record.
    """

    content: str
    category: MemoryCategory
    origin: str = "System"
    importance: float = 0.50
    confidence: float = 1.0
    retention_policy: RetentionPolicy = RetentionPolicy.CLINICAL
    related_entities: List[str] = field(default_factory=list)
    related_experiences: List[str] = field(default_factory=list)
    knowledge_references: List[str] = field(default_factory=list)
    context_snapshot: Dict[str, Any] = field(default_factory=dict)
    memory_id: str = field(default_factory=lambda: f"mem-{uuid.uuid4().hex[:8]}")
    timestamp_iso: str = field(default_factory=lambda: datetime.now().isoformat())
    created_ts: float = field(default_factory=time.time)
    version: int = 1
    is_archived: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "category": self.category.value,
            "origin": self.origin,
            "importance": round(self.importance, 3),
            "confidence": round(self.confidence, 3),
            "retention_policy": self.retention_policy.value,
            "related_entities": list(self.related_entities),
            "related_experiences": list(self.related_experiences),
            "knowledge_references": list(self.knowledge_references),
            "timestamp_iso": self.timestamp_iso,
            "version": self.version,
            "is_archived": self.is_archived,
        }


@dataclass
class ReconstructedContext:
    """
    Reconstructed cognitive context snapshot surrounding a recalled memory.
    """

    memory_id: str
    surrounding_events: List[str]
    knowledge_facts: List[str]
    executive_decisions: List[str]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "surrounding_events": self.surrounding_events,
            "knowledge_facts": self.knowledge_facts,
            "executive_decisions": self.executive_decisions,
            "explanation": self.explanation,
        }
