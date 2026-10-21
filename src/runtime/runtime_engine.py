"""
MEMORA Central Runtime Engine.

Orchestrates RuntimeConfigurationManager, ServiceRegistry, RuntimeScheduler, FaultManager,
RecoveryOrchestrator, RuntimeMetricsAggregator, RuntimeHealthGenerator, and RuntimeExplainer.

Sole owner of operational lifecycle management. Inherits from ICognitiveSubsystem.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from src.core.interfaces import ICognitiveSubsystem
from src.runtime.runtime_configuration import RuntimeConfigurationManager, RuntimeProfile
from src.runtime.service_registry import ServiceRegistry
from src.runtime.runtime_scheduler import RuntimeScheduler
from src.runtime.fault_manager import FaultManager
from src.runtime.recovery_orchestrator import RecoveryOrchestrator
from src.runtime.runtime_metrics import RuntimeMetricsAggregator
from src.runtime.runtime_health import RuntimeHealthGenerator
from src.runtime.runtime_explainer import RuntimeExplainer


class CentralRuntimeEngine(ICognitiveSubsystem):
    """
    Central Clinical Runtime & Operational Subsystem Orchestrator.
    """

    def __init__(self, profile: RuntimeProfile = RuntimeProfile.CLINICAL_DEMO) -> None:
        self.config_manager = RuntimeConfigurationManager(profile=profile)
        self.service_registry = ServiceRegistry()
        self.scheduler = RuntimeScheduler()
        self.fault_manager = FaultManager()
        self.recovery_orchestrator = RecoveryOrchestrator(self.service_registry)
        self.metrics_aggregator = RuntimeMetricsAggregator()
        self._cycle_counter = 0
        self._status = "INITIALIZED"
        self._lock = threading.Lock()

    def initialize(self) -> bool:
        with self._lock:
            self._status = "RUNNING"
            return True

    def shutdown(self) -> bool:
        with self._lock:
            self._status = "SHUTDOWN"
            self.service_registry.shutdown_all()
            return True

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.process_cycle()

    def status(self) -> str:
        with self._lock:
            return self._status

    def health(self) -> Dict[str, Any]:
        with self._lock:
            return RuntimeHealthGenerator.generate_health_report(
                self.config_manager,
                self.service_registry,
                self.fault_manager,
                self.metrics_aggregator,
            )

    def metrics(self) -> Dict[str, Any]:
        with self._lock:
            res = self.metrics_aggregator.capture_metrics()
            res["cycle_count"] = self._cycle_counter
            return res

    def explain(self) -> str:
        h = self.health()
        return f"Runtime Engine: Operational Status is '{h['overall_status']}' under Profile '{h['runtime_profile']}'."

    def process_cycle(self) -> Dict[str, Any]:
        """
        Execute one operational cycle of telemetry collection, health generation, and scheduling ticks.
        """
        start_ts = time.time()
        with self._lock:
            self._cycle_counter += 1

        # 1. Tick scheduler tasks
        self.scheduler.tick(current_ts=start_ts)

        # 2. Capture operational metrics & health summary
        health_report = self.health()

        # 3. Generate structured log example
        structured_log = RuntimeExplainer.create_structured_log(
            subsystem="CentralRuntimeEngine",
            operation="process_cycle",
            correlation_id=f"corr-cycle-{self._cycle_counter}",
            execution_duration_ms=(time.time() - start_ts) * 1000.0,
        )

        latency_ms = round((time.time() - start_ts) * 1000.0, 3)

        return {
            "cycle": self._cycle_counter,
            "runtime_health": health_report,
            "structured_log_sample": structured_log,
            "runtime_latency_ms": latency_ms,
        }

    def reset(self) -> None:
        with self._lock:
            self._cycle_counter = 0
            self.fault_manager.clear()
