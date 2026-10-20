"""
MEMORA Service Registry.

Provides thread-safe service registration and operational status tracking for all cognitive subsystems.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from src.core.interfaces import ICognitiveSubsystem


class ServiceRegistry:
    """
    Thread-safe registry for cognitive services and subsystem drivers.
    """

    def __init__(self) -> None:
        self._services: Dict[str, ICognitiveSubsystem] = {}
        self._lock = threading.Lock()

    def register_service(self, name: str, service: ICognitiveSubsystem) -> None:
        with self._lock:
            self._services[name] = service
            service.initialize()

    def get_service(self, name: str) -> Optional[ICognitiveSubsystem]:
        with self._lock:
            return self._services.get(name)

    def get_all_services(self) -> Dict[str, ICognitiveSubsystem]:
        with self._lock:
            return dict(self._services)

    def shutdown_all(self) -> None:
        with self._lock:
            for s in self._services.values():
                s.shutdown()

    def get_health_status(self) -> Dict[str, Any]:
        with self._lock:
            statuses = {name: s.status() for name, s in self._services.items()}
            healthy = all(st in ("RUNNING", "INITIALIZED") for st in statuses.values())
            return {
                "overall_health": "HEALTHY" if healthy else "DEGRADED",
                "registered_services_count": len(self._services),
                "services": statuses,
            }
