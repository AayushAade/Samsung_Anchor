"""
MEMORA Cognitive Health Monitoring Aggregator.

Provides repository-wide cognitive health monitoring and metrics aggregation:
- Subsystem availability & status tracking
- Processing latency benchmarks
- Event queue depth & throughput
- Resource utilisation & error tracking
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional


class CognitiveHealthMonitor:
    """
    Repository-wide health diagnostic and metrics aggregator.
    """

    def __init__(self) -> None:
        self._subsystem_statuses: Dict[str, str] = {
            "CognitiveOperatingSystem": "RUNNING",
            "TrustAndSafety": "RUNNING",
            "BehaviourIntelligence": "RUNNING",
            "CognitiveReasoning": "RUNNING",
            "ExecutiveFunction": "RUNNING",
            "ExperienceLearning": "RUNNING",
        }
        self._latencies: Dict[str, float] = {}
        self._error_counts: Dict[str, int] = {k: 0 for k in self._subsystem_statuses}
        self._lock = threading.Lock()

    def record_subsystem_health(
        self, subsystem_name: str, status: str, latency_ms: float = 0.0, error_occurred: bool = False
    ) -> None:
        with self._lock:
            self._subsystem_statuses[subsystem_name] = status
            self._latencies[subsystem_name] = latency_ms
            if error_occurred:
                self._error_counts[subsystem_name] = self._error_counts.get(subsystem_name, 0) + 1

    def get_health_summary(self) -> Dict[str, Any]:
        with self._lock:
            overall = "HEALTHY" if all(s == "RUNNING" for s in self._subsystem_statuses.values()) else "DEGRADED"
            avg_lat = sum(self._latencies.values()) / max(1, len(self._latencies))
            total_errors = sum(self._error_counts.values())

            return {
                "overall_status": overall,
                "active_subsystems_count": len(self._subsystem_statuses),
                "subsystem_statuses": dict(self._subsystem_statuses),
                "average_latency_ms": round(avg_lat, 3),
                "total_errors_count": total_errors,
                "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
