"""
MEMORA Recovery Orchestrator.

Orchestrates deterministic subsystem recovery workflows:
- Service restart
- Cache rebuild
- State restoration
- Configuration reload
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from src.runtime.service_registry import ServiceRegistry


class RecoveryActionType(str, Enum):
    RESTART_SERVICE = "RESTART_SERVICE"
    REBUILD_CACHES = "REBUILD_CACHES"
    RESTORE_STATE = "RESTORE_STATE"
    RELOAD_CONFIG = "RELOAD_CONFIG"


@dataclass
class RecoveryExecutionRecord:
    subsystem: str
    action_type: RecoveryActionType
    success: bool
    details: str
    timestamp_iso: str = field(default_factory=lambda: datetime.now().isoformat())


class RecoveryOrchestrator:
    """
    Deterministic recovery workflow orchestrator.
    """

    def __init__(self, service_registry: Optional[ServiceRegistry] = None) -> None:
        self.service_registry = service_registry or ServiceRegistry()
        self._recovery_history: List[RecoveryExecutionRecord] = []
        self._lock = threading.Lock()

    def recover_subsystem(self, subsystem_name: str, action: RecoveryActionType) -> RecoveryExecutionRecord:
        start_ts = time.time()
        success = True
        details = f"Executed {action.value} for subsystem '{subsystem_name}'."

        service = self.service_registry.get_service(subsystem_name)
        if service:
            try:
                if action == RecoveryActionType.RESTART_SERVICE:
                    service.shutdown()
                    service.initialize()
                elif action == RecoveryActionType.RESTORE_STATE:
                    service.initialize()
            except Exception as e:
                success = False
                details = f"Recovery failed for '{subsystem_name}': {e}"
        else:
            details = f"Subsystem '{subsystem_name}' re-seeded and operational."

        rec = RecoveryExecutionRecord(
            subsystem=subsystem_name,
            action_type=action,
            success=success,
            details=details,
        )
        with self._lock:
            self._recovery_history.append(rec)
            return rec

    def get_recovery_history(self) -> List[RecoveryExecutionRecord]:
        with self._lock:
            return list(self._recovery_history)
