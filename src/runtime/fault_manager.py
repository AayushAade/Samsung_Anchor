"""
MEMORA Subsystem Fault Isolation Manager.

Isolates subsystem exceptions, prevents full platform crashes,
and logs structured fault records for operational diagnostics.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class FaultRecord:
    subsystem: str
    error_message: str
    stack_trace: str = ""
    severity: str = "ERROR"
    fault_id: str = field(default_factory=lambda: f"flt-{datetime.now().strftime('%H%M%S')}")
    timestamp_iso: str = field(default_factory=lambda: datetime.now().isoformat())


class FaultManager:
    """
    Thread-safe fault isolation and error boundary manager.
    """

    def __init__(self) -> None:
        self._faults: List[FaultRecord] = []
        self._subsystem_fault_counts: Dict[str, int] = {}
        self._lock = threading.Lock()

    def record_fault(self, subsystem: str, error: Exception, severity: str = "ERROR") -> FaultRecord:
        rec = FaultRecord(
            subsystem=subsystem,
            error_message=str(error),
            severity=severity,
        )
        with self._lock:
            self._faults.append(rec)
            self._subsystem_fault_counts[subsystem] = self._subsystem_fault_counts.get(subsystem, 0) + 1
            return rec

    def is_subsystem_degraded(self, subsystem: str, threshold: int = 3) -> bool:
        with self._lock:
            return self._subsystem_fault_counts.get(subsystem, 0) >= threshold

    def get_fault_history(self) -> List[FaultRecord]:
        with self._lock:
            return list(self._faults)

    def clear(self) -> None:
        with self._lock:
            self._faults.clear()
            self._subsystem_fault_counts.clear()
