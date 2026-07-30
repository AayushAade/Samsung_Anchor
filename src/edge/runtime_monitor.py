"""
MEMORA Edge Runtime Health Monitor.

Tracks edge execution health, battery thresholds, storage availability, and capability
degradation without operating system hooks or platform APIs.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List

from src.edge.edge_models import Capability, DeviceProfile, RuntimeState


class RuntimeMonitor:
    """
    Thread-safe runtime health evaluator.
    Evaluates battery thresholds, storage pressure, and offline mode indicators.
    """

    def __init__(self) -> None:
        self._warnings: List[str] = []
        self._evaluation_count = 0
        self._lock = threading.Lock()

    def evaluate_health(
        self,
        profile: DeviceProfile,
        network_available: bool = True,
    ) -> RuntimeState:
        """
        Evaluate overall runtime state based on battery, storage, and network availability.
        """
        warnings: List[str] = []
        state = RuntimeState.READY

        with self._lock:
            self._evaluation_count += 1

            # Battery evaluation
            if profile.battery_level <= 10.0:
                state = RuntimeState.LOW_POWER
                warnings.append(f"Critical low battery level ({profile.battery_level:.1f}%).")
            elif profile.battery_level <= 20.0:
                state = RuntimeState.DEGRADED
                warnings.append(f"Low battery level ({profile.battery_level:.1f}%).")

            # Storage evaluation
            if profile.available_storage < 50.0:
                if state != RuntimeState.LOW_POWER:
                    state = RuntimeState.DEGRADED
                warnings.append(f"Storage pressure: only {profile.available_storage:.1f} MB remaining.")

            # Network / Offline state evaluation
            if not network_available or Capability.NETWORK not in profile.capabilities:
                if state == RuntimeState.READY:
                    state = RuntimeState.OFFLINE
                warnings.append("Operating in offline-first mode.")

            self._warnings = warnings
            return state

    def has_warnings(self) -> bool:
        """Return True if active warnings are present."""
        with self._lock:
            return len(self._warnings) > 0

    def get_warnings(self) -> List[str]:
        """Return active health warnings."""
        with self._lock:
            return list(self._warnings)

    def get_evaluation_count(self) -> int:
        """Return total number of health evaluations performed."""
        with self._lock:
            return self._evaluation_count

    def clear(self) -> None:
        """Clear active health warnings and evaluation counts."""
        with self._lock:
            self._warnings.clear()
            self._evaluation_count = 0
