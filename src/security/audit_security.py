"""
MEMORA Security Audit Logger.

Provides thread-safe, append-only security audit log entries for identity access tracking.
Does not persist to disk or rely on external database libraries.
"""

from __future__ import annotations

import threading
from typing import List, Optional

from src.security.security_models import SecurityAuditEntry


class AuditSecurity:
    """
    Thread-safe security audit event logger.
    """

    MAX_ENTRIES = 1000

    def __init__(self, max_entries: int = 1000) -> None:
        self.max_entries = max_entries
        self._entries: List[SecurityAuditEntry] = []
        self._lock = threading.Lock()

    def record_audit(
        self,
        identity_id: str,
        requested_operation: str,
        granted: bool,
        denial_reason: str = "",
    ) -> SecurityAuditEntry:
        entry = SecurityAuditEntry(
            identity_id=identity_id,
            requested_operation=requested_operation,
            granted=granted,
            denial_reason=denial_reason,
        )
        with self._lock:
            self._entries.append(entry)
            if len(self._entries) > self.max_entries:
                self._entries = self._entries[-self.max_entries:]
            return entry

    def get_entries(self) -> List[SecurityAuditEntry]:
        with self._lock:
            return list(self._entries)

    def get_denied_entries(self) -> List[SecurityAuditEntry]:
        with self._lock:
            return [e for e in self._entries if not e.granted]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
