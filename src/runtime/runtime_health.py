"""
MEMORA System-Wide Runtime Health Generator.

Combines service registry status, fault manager history, resource metrics,
and active configuration profile into a unified operational health report.
"""

from __future__ import annotations

import time
from typing import Any, Dict

from src.runtime.fault_manager import FaultManager
from src.runtime.runtime_configuration import RuntimeConfigurationManager
from src.runtime.runtime_metrics import RuntimeMetricsAggregator
from src.runtime.service_registry import ServiceRegistry


class RuntimeHealthGenerator:
    """
    Generates unified runtime health reports.
    """

    @classmethod
    def generate_health_report(
        cls,
        config_mgr: RuntimeConfigurationManager,
        service_registry: ServiceRegistry,
        fault_manager: FaultManager,
        metrics_aggregator: RuntimeMetricsAggregator,
    ) -> Dict[str, Any]:
        config = config_mgr.get_config()
        service_health = service_registry.get_health_status()
        fault_history = fault_manager.get_fault_history()
        resource_metrics = metrics_aggregator.capture_metrics()

        overall = "HEALTHY"
        if len(fault_history) > 5 or service_health["overall_health"] != "HEALTHY":
            overall = "DEGRADED"

        return {
            "overall_status": overall,
            "runtime_profile": config.profile.value,
            "services_health": service_health,
            "total_faults_recorded": len(fault_history),
            "resource_metrics": resource_metrics,
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
