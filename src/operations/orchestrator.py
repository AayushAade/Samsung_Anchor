"""
MEMORA System Orchestrator & Operational Control Backbone.

Coordinates subsystem registrations, health statuses, metrics aggregation,
and decouples subsystem components via the operational control plane.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import threading
import time
from typing import Any

from src.operations.operational_event_bus import OperationalEventBus, OperationalEventType


@dataclass
class SubsystemState:
    """Represents operational state metadata for a registered subsystem."""
    name: str
    status: str = "READY"                    # READY, HEALTHY, WARNING, FAILED, DISABLED
    health_msg: str = "Subsystem operating normally"
    version: str = "1.0.0"
    dependencies: list[str] = field(default_factory=list)
    startup_time: float = field(default_factory=time.time)
    last_execution_iso: str = "N/A"
    last_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        uptime = time.time() - self.startup_time
        return {
            "name": self.name,
            "status": self.status,
            "health_msg": self.health_msg,
            "version": self.version,
            "dependencies": self.dependencies,
            "startup_timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.startup_time)),
            "uptime_seconds": round(uptime, 2),
            "last_execution": self.last_execution_iso,
            "last_error": self.last_error,
        }


class SystemOrchestrator:
    """
    Central operational orchestrator and subsystem health registry.
    """

    _instance: SystemOrchestrator | None = None
    _lock = threading.Lock()

    def __new__(cls) -> SystemOrchestrator:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._subsystems: dict[str, SubsystemState] = {}
                cls._instance._registry_lock = threading.Lock()
                cls._instance.event_bus = OperationalEventBus()
                cls._instance._init_default_subsystems()
            return cls._instance

    def _init_default_subsystems(self) -> None:
        """Register default MEMORA core subsystems."""
        defaults = [
            ("Vision Pipeline", ["OpenCV Camera HAL"], "1.1.0"),
            ("Face Recognizer", ["FAISS Vector Store", "SQLite DB"], "1.1.0"),
            ("FAISS Vector Store", ["OpenMP C++ Lib"], "1.1.0"),
            ("SQLite Memory Layer", ["SQLAlchemy ORM"], "1.1.0"),
            ("Patient State Engine", ["Clinical Care Policy"], "1.1.0"),
            ("Care Policy Framework", ["Patient State Engine"], "1.1.0"),
            ("Explainability Engine", ["Decision Timeline"], "1.1.0"),
            ("Audio Listener", ["PyAudio HAL"], "1.1.0"),
            ("Speaker HAL", ["PyTTSx3 Engine"], "1.1.0"),
            ("Experience Server", ["WebSockets Port 8765"], "1.1.0"),
        ]
        for name, deps, ver in defaults:
            self.register_subsystem(name, dependencies=deps, version=ver)

    def register_subsystem(self, name: str, dependencies: list[str] | None = None, version: str = "1.0.0") -> None:
        """Register a subsystem in the central orchestrator."""
        with self._registry_lock:
            if name not in self._subsystems:
                state = SubsystemState(name=name, dependencies=dependencies or [], version=version)
                self._subsystems[name] = state
                self.event_bus.publish(OperationalEventType.SUBSYSTEM_STARTED, name, {"status": "READY"})

    def update_subsystem_status(
        self, name: str, status: str, health_msg: str, last_error: str | None = None
    ) -> None:
        """Update operational status and health message for a registered subsystem."""
        with self._registry_lock:
            if name in self._subsystems:
                sub = self._subsystems[name]
                sub.status = status
                sub.health_msg = health_msg
                sub.last_execution_iso = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                if last_error:
                    sub.last_error = last_error
                    self.event_bus.publish(OperationalEventType.SUBSYSTEM_FAILED, name, {"error": last_error})

    def get_all_subsystem_statuses(self) -> dict[str, dict[str, Any]]:
        """Fetch status dictionary for all registered subsystems."""
        with self._registry_lock:
            return {name: sub.to_dict() for name, sub in self._subsystems.items()}

    def get_system_health_summary(self) -> dict[str, Any]:
        """Generate high-level overall system health summary."""
        statuses = self.get_all_subsystem_statuses()
        total = len(statuses)
        healthy_count = sum(1 for s in statuses.values() if s["status"] in ("READY", "HEALTHY"))
        warning_count = sum(1 for s in statuses.values() if s["status"] == "WARNING")
        failed_count = sum(1 for s in statuses.values() if s["status"] == "FAILED")

        overall = "HEALTHY"
        if failed_count > 0:
            overall = "FAILED"
        elif warning_count > 0:
            overall = "WARNING"

        return {
            "overall_status": overall,
            "total_subsystems": total,
            "healthy_count": healthy_count,
            "warning_count": warning_count,
            "failed_count": failed_count,
            "subsystems": statuses,
        }
