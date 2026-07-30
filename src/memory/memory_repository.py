"""
MEMORA Thread-Safe Memory Repository.

Manages active and archived memory records with append-only integrity and recoverability.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from src.memory.memory_models import MemoryCategory, MemoryRecord, RetentionPolicy


class MemoryRepository:
    """
    Thread-safe repository for cognitive memory records.
    """

    def __init__(self) -> None:
        self._active_memories: Dict[str, MemoryRecord] = {}
        self._archived_memories: Dict[str, MemoryRecord] = {}
        self._lock = threading.Lock()
        self._seed_baseline_memories()

    def add_record(self, record: MemoryRecord) -> MemoryRecord:
        with self._lock:
            self._active_memories[record.memory_id] = record
            return record

    def get_record(self, memory_id: str) -> Optional[MemoryRecord]:
        with self._lock:
            return self._active_memories.get(memory_id) or self._archived_memories.get(memory_id)

    def get_all_active(self) -> List[MemoryRecord]:
        with self._lock:
            return list(self._active_memories.values())

    def get_all_archived(self) -> List[MemoryRecord]:
        with self._lock:
            return list(self._archived_memories.values())

    def archive_record(self, memory_id: str) -> Optional[MemoryRecord]:
        with self._lock:
            rec = self._active_memories.pop(memory_id, None)
            if rec:
                rec.is_archived = True
                self._archived_memories[memory_id] = rec
                return rec
            return None

    def restore_record(self, memory_id: str) -> Optional[MemoryRecord]:
        with self._lock:
            rec = self._archived_memories.pop(memory_id, None)
            if rec:
                rec.is_archived = False
                self._active_memories[memory_id] = rec
                return rec
            return None

    def clear(self) -> None:
        with self._lock:
            self._active_memories.clear()
            self._archived_memories.clear()

    def _seed_baseline_memories(self) -> None:
        """Seed baseline cognitive memories."""
        m1 = MemoryRecord(
            memory_id="mem-baseline-1",
            content="Reading glasses located on coffee table in Living Room",
            category=MemoryCategory.OBSERVATION,
            importance=0.85,
            related_entities=["Reading Glasses", "Living Room"],
        )
        m2 = MemoryRecord(
            memory_id="mem-baseline-2",
            content="Morning Donepezil 10mg medication prescribed for Margaret",
            category=MemoryCategory.KNOWLEDGE_FACT,
            importance=0.95,
            retention_policy=RetentionPolicy.CLINICAL,
            related_entities=["Donepezil Medication", "Margaret"],
        )
        self._active_memories[m1.memory_id] = m1
        self._active_memories[m2.memory_id] = m2
