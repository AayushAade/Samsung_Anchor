"""
MEMORA Operational Event Bus.

Decoupled event broadcasting system for real-time subsystem state changes,
recognition completions, memory recalls, and system failure events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import threading
import time
from typing import Any, Callable


class OperationalEventType(str, Enum):
    RECOGNITION_COMPLETED = "RecognitionCompleted"
    MEMORY_RETRIEVED = "MemoryRetrieved"
    OBJECT_DETECTED = "ObjectDetected"
    PATIENT_STATE_CHANGED = "PatientStateChanged"
    CARE_POLICY_SELECTED = "CarePolicySelected"
    SPEECH_COMPLETED = "SpeechCompleted"
    SUBSYSTEM_STARTED = "SubsystemStarted"
    SUBSYSTEM_STOPPED = "SubsystemStopped"
    SUBSYSTEM_FAILED = "SubsystemFailed"


@dataclass
class OperationalEvent:
    """Represents an operational event in the MEMORA control plane."""
    event_type: OperationalEventType
    subsystem: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp_iso: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "subsystem": self.subsystem,
            "payload": self.payload,
            "timestamp": self.timestamp_iso,
        }


class OperationalEventBus:
    """
    Thread-safe operational event bus.
    """

    _instance: OperationalEventBus | None = None
    _lock = threading.Lock()

    def __new__(cls) -> OperationalEventBus:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._listeners = []
                cls._instance._bus_lock = threading.Lock()
            return cls._instance

    def subscribe(self, listener: Callable[[OperationalEvent], None]) -> None:
        """Register a callback listener for operational events."""
        with self._bus_lock:
            if listener not in self._listeners:
                self._listeners.append(listener)

    def publish(self, event_type: OperationalEventType, subsystem: str, payload: dict[str, Any] | None = None) -> None:
        """Publish an operational event to all registered listeners."""
        event = OperationalEvent(event_type=event_type, subsystem=subsystem, payload=payload or {})
        with self._bus_lock:
            listeners = list(self._listeners)

        for listener in listeners:
            try:
                listener(event)
            except Exception:
                pass
