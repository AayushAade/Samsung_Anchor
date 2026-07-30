"""
MEMORA Deterministic Resource Policy Manager.

Evaluates resource constraint policies (Low Battery, Storage Pressure) and returns
preservation recommendations without operating system hooks.
"""

from __future__ import annotations

import threading
from typing import List, Tuple


class ResourceManager:
    """
    Thread-safe resource policy evaluator.
    Applies deterministic preservation policy rules based on battery level and available storage.
    """

    def __init__(self) -> None:
        self._policy_history: List[Tuple[float, float, List[str]]] = []
        self._lock = threading.Lock()

    def evaluate_resource_policies(
        self,
        battery_level: float,
        available_storage_mb: float,
    ) -> List[str]:
        """
        Evaluate battery and storage conditions against deterministic preservation policies.
        Returns list of recommended resource preservation actions.
        """
        actions: List[str] = []

        with self._lock:
            # 1. Battery Policies
            if battery_level <= 10.0:
                actions.append(
                    "Policy #1a: Critical battery (<=10%) -> Suspend background diagnostic loops & preserve patient assistance workflows."
                )
                actions.append("Policy #1b: Throttle telemetry streaming interval to 10000ms -> Maximize remaining runtime.")
            elif battery_level <= 20.0:
                actions.append(
                    "Policy #2: Low battery (<=20%) -> Disable non-essential background diagnostics & reduce display brightness."
                )
            elif battery_level <= 35.0:
                actions.append("Policy #3: Moderate battery (<=35%) -> Disable continuous video frame caching.")

            # 2. Storage Policies
            if available_storage_mb <= 50.0:
                actions.append(
                    "Policy #4a: Critical storage (<=50 MB) -> Rotate oldest audit log files & compress session trace cache."
                )
                actions.append("Policy #4b: Preserve long-term memory database & clinical knowledge graph integrity.")
            elif available_storage_mb <= 150.0:
                actions.append("Policy #5: Low storage (<=150 MB) -> Purge temporary cache files.")

            if not actions:
                actions.append("Policy #0: Resource levels within normal operational thresholds -> No action required.")

            self._policy_history.append((battery_level, available_storage_mb, actions))
            return actions

    def get_latest_evaluation(self) -> List[str]:
        """Return the most recently evaluated list of policy actions."""
        with self._lock:
            return list(self._policy_history[-1][2]) if self._policy_history else []

    def get_policy_history(self) -> List[Tuple[float, float, List[str]]]:
        """Return history of evaluated resource policies."""
        with self._lock:
            return list(self._policy_history)

    def clear(self) -> None:
        """Clear policy evaluation history."""
        with self._lock:
            self._policy_history.clear()
