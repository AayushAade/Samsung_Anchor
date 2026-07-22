from typing import Dict, Any


class MetricsCollector:
    """
    Real-time operational metrics and telemetry collector.
    """

    def __init__(self) -> None:
        self.total_cycles: int = 0
        self.last_latency_ms: float = 45.0
        self.perception_events_count: int = 0
        self.medication_reminders_count: int = 0
        self.emergency_alerts_count: int = 0
        self.errors_count: int = 0

    def record_cycle(self, latency_ms: float = 45.0) -> None:
        self.total_cycles += 1
        self.last_latency_ms = latency_ms

    def record_perception_event(self) -> None:
        self.perception_events_count += 1

    def record_medication_reminder(self) -> None:
        self.medication_reminders_count += 1

    def record_emergency_alert(self) -> None:
        self.emergency_alerts_count += 1

    def record_error(self) -> None:
        self.errors_count += 1

    def get_metrics_summary(self) -> Dict[str, Any]:
        return {
            "total_cycles": self.total_cycles,
            "last_latency_ms": self.last_latency_ms,
            "perception_events": self.perception_events_count,
            "medication_reminders": self.medication_reminders_count,
            "emergency_alerts": self.emergency_alerts_count,
            "errors_count": self.errors_count,
        }
