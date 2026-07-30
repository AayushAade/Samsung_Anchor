"""
MEMORA Deterministic I/O Message Router.

Routes incoming and outgoing IOMessage envelopes to target subsystem destinations
using a 100% deterministic routing mapping matrix without heuristics or ML.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from src.io.io_models import IOMessage, InputType, OutputType, RoutingDecision


# Deterministic ingress routing mapping matrix
INPUT_ROUTING_MAP: Dict[InputType, str] = {
    InputType.CAMERA: "PerceptionManager",
    InputType.MICROPHONE: "AudioPipeline",
    InputType.SENSOR: "SensorBus",
    InputType.TEXT: "DialogueManager",
    InputType.SYSTEM: "CentralRuntimeEngine",
    InputType.CLINICAL: "ClinicalEvaluator",
    InputType.EXTERNAL: "CognitivePipeline",
}

# Deterministic egress routing mapping matrix
OUTPUT_ROUTING_MAP: Dict[OutputType, str] = {
    OutputType.DISPLAY: "DisplayAdapter",
    OutputType.AUDIO: "SpeakerAdapter",
    OutputType.ALERT: "SafetyManager",
    OutputType.LOG: "AuditLogger",
    OutputType.REPORT: "ClinicalReportGenerator",
    OutputType.SYSTEM: "CentralRuntimeEngine",
    OutputType.CLINICAL: "ClinicalStream",
}


class IORouter:
    """
    Thread-safe deterministic message router.
    """

    def __init__(self) -> None:
        self._routed_decisions: List[RoutingDecision] = []
        self._lock = threading.Lock()

    def route(self, message: IOMessage) -> RoutingDecision:
        destination = message.destination
        reason = ""
        accepted = True
        status = "ROUTED"

        if message.input_type is not None:
            mapped_dest = INPUT_ROUTING_MAP.get(message.input_type, message.destination)
            destination = mapped_dest
            reason = f"Mapped InputType `{message.input_type.value}` to destination `{destination}`."
        elif message.output_type is not None:
            mapped_dest = OUTPUT_ROUTING_MAP.get(message.output_type, message.destination)
            destination = mapped_dest
            reason = f"Mapped OutputType `{message.output_type.value}` to destination `{destination}`."
        else:
            reason = f"Routed directly to destination `{destination}`."

        decision = RoutingDecision(
            destination=destination,
            accepted=accepted,
            reason=reason,
            validation_status=status,
        )

        with self._lock:
            self._routed_decisions.append(decision)
            return decision

    def get_routed_decisions(self) -> List[RoutingDecision]:
        with self._lock:
            return list(self._routed_decisions)

    def clear(self) -> None:
        with self._lock:
            self._routed_decisions.clear()
