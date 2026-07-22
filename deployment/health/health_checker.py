from enum import Enum
from typing import Dict, Any


class HealthStatus(Enum):
    HEALTHY = "Healthy"
    DEGRADED = "Degraded"
    CRITICAL = "Critical"


class HealthChecker:
    """
    Multi-component readiness and health checker.
    Evaluates Runtime, Perception, Cognition, and Clinical systems.
    """

    def __init__(self) -> None:
        self._statuses: Dict[str, bool] = {
            "runtime_ready": True,
            "perception_ready": True,
            "cognition_ready": True,
            "clinical_ready": True,
        }

    def check_health(self) -> Dict[str, Any]:
        overall = self.get_overall_status()
        return {
            "overall_status": overall.value,
            "runtime_ready": self._statuses["runtime_ready"],
            "perception_ready": self._statuses["perception_ready"],
            "cognition_ready": self._statuses["cognition_ready"],
            "clinical_ready": self._statuses["clinical_ready"],
        }

    def set_component_health(self, component: str, ready: bool) -> None:
        if component in self._statuses:
            self._statuses[component] = ready

    def get_overall_status(self) -> HealthStatus:
        ready_count = sum(1 for v in self._statuses.values() if v)
        if ready_count == len(self._statuses):
            return HealthStatus.HEALTHY
        elif ready_count >= 2:
            return HealthStatus.DEGRADED
        return HealthStatus.CRITICAL
