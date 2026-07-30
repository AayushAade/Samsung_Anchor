"""
Cognitive Operating System — Working Memory.

Temporary cognitive state storage with automatic TTL-based expiration.
Stores short-lived slots (current conversation topic, active search target,
pending reminder) that should never pollute long-term memory.

Thread-safe. No external dependencies.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from src.cognition.cos.models import WorkingMemorySlot


class WorkingMemory:
    """
    Slot-based temporary cognitive storage with configurable TTL expiration.

    Each slot has an independent time-to-live. Stale slots are garbage-collected
    at the start of every kernel reasoning cycle via ``expire_stale()``.
    """

    MAX_SLOTS = 20
    DEFAULT_TTL = 300.0  # 5 minutes

    def __init__(self) -> None:
        self._slots: dict[str, WorkingMemorySlot] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        """
        Store or overwrite a working memory slot.

        Parameters
        ----------
        key : str
            Slot identifier (e.g., ``"current_conversation"``, ``"active_search"``).
        value : Any
            The cognitive state to hold temporarily.
        ttl_seconds : float, optional
            Time-to-live in seconds. Defaults to ``DEFAULT_TTL``.
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.DEFAULT_TTL
        with self._lock:
            self._slots[key] = WorkingMemorySlot(
                key=key, value=value, stored_at=time.time(), ttl_seconds=ttl,
            )
            self._enforce_capacity()

    def recall(self, key: str) -> Any | None:
        """
        Recall a working memory slot value. Returns ``None`` if absent or expired.
        """
        with self._lock:
            slot = self._slots.get(key)
            if slot is None or slot.is_expired:
                return None
            return slot.value

    def expire_stale(self) -> int:
        """
        Remove all expired slots. Returns the number of slots evicted.
        Called at the start of every kernel reasoning cycle.
        """
        with self._lock:
            before = len(self._slots)
            self._slots = {
                k: v for k, v in self._slots.items() if not v.is_expired
            }
            return before - len(self._slots)

    def snapshot(self) -> dict[str, Any]:
        """
        Return a serialisable snapshot of all active (non-expired) slots.
        """
        with self._lock:
            return {
                "slot_count": len(self._slots),
                "slots": {
                    k: v.to_dict()
                    for k, v in self._slots.items()
                    if not v.is_expired
                },
            }

    def clear(self) -> None:
        """Remove all slots."""
        with self._lock:
            self._slots.clear()

    @property
    def active_slot_count(self) -> int:
        with self._lock:
            return sum(1 for v in self._slots.values() if not v.is_expired)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _enforce_capacity(self) -> None:
        """Drop oldest slots if capacity exceeded."""
        while len(self._slots) > self.MAX_SLOTS:
            oldest_key = min(self._slots, key=lambda k: self._slots[k].stored_at)
            del self._slots[oldest_key]
