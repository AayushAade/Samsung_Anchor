"""
MEMORA Forgetting Manager.

Executes deterministic archiving of expired memories according to retention policy:
- Flushes expired memories with structured audit log
- Preserves 100% recoverability (archived memories can be restored)
- Never permanently deletes records without explicit caregiver authorization
"""

from __future__ import annotations

import time
from typing import List, Tuple

from src.memory.memory_models import MemoryRecord
from src.memory.memory_repository import MemoryRepository
from src.memory.retention_manager import RetentionManager


class ForgettingManager:
    """
    Deterministic memory archiving and recovery manager.
    """

    def __init__(self, repository: MemoryRepository) -> None:
        self.repository = repository
        self._audit_log: List[str] = []

    def evaluate_and_archive_expired(self, current_ts: float = 0.0) -> Tuple[List[MemoryRecord], List[str]]:
        """
        Scan active memories and archive any that have expired.
        Returns (archived_memories, audit_log_entries).
        """
        active = self.repository.get_all_active()
        archived: List[MemoryRecord] = []
        new_audit: List[str] = []

        now = current_ts or time.time()
        for rec in active:
            if RetentionManager.is_expired(rec, current_ts=now):
                archived_rec = self.repository.archive_record(rec.memory_id)
                if archived_rec:
                    archived.append(archived_rec)
                    msg = f"Archived expired memory `{rec.memory_id}` (Policy: {rec.retention_policy.value}) at timestamp {now:.0f}."
                    new_audit.append(msg)
                    self._audit_log.append(msg)

        return (archived, new_audit)

    def recover_archived_memory(self, memory_id: str) -> Tuple[Optional[MemoryRecord], str]:
        """
        Recover an archived memory record back to active status.
        """
        restored = self.repository.restore_record(memory_id)
        if restored:
            msg = f"Recovered archived memory `{memory_id}` back to active repository."
            self._audit_log.append(msg)
            return (restored, msg)
        return (None, f"Archived memory `{memory_id}` not found.")
