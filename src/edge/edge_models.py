"""
MEMORA Edge Runtime & Device Integration Framework Data Models.

Defines immutable value objects, device classifications, abstract capabilities,
runtime health states, device profiles, and snapshot schemas.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class DeviceType(str, Enum):
    """
    Classifies supported hardware deployment form-factors.
    """

    PHONE = "PHONE"
    SMARTWATCH = "SMARTWATCH"
    SMART_GLASSES = "SMART_GLASSES"
    TABLET = "TABLET"
    EDGE_COMPUTER = "EDGE_COMPUTER"

    def is_wearable(self) -> bool:
        """Return True if device is a wearable form-factor."""
        return self in (DeviceType.SMARTWATCH, DeviceType.SMART_GLASSES)

    def requires_haptic(self) -> bool:
        """Return True if device typically relies on haptic feedback (Smartwatch)."""
        return self == DeviceType.SMARTWATCH


class Capability(str, Enum):
    """
    Standardized abstract hardware capability flags.
    """

    CAMERA = "CAMERA"
    MICROPHONE = "MICROPHONE"
    SPEAKER = "SPEAKER"
    DISPLAY = "DISPLAY"
    HAPTIC = "HAPTIC"
    STORAGE = "STORAGE"
    NETWORK = "NETWORK"
    GPS = "GPS"

    def is_essential(self) -> bool:
        """Return True if capability is essential for basic patient interaction."""
        return self in (Capability.MICROPHONE, Capability.SPEAKER, Capability.STORAGE)

    def is_sensor_input(self) -> bool:
        """Return True if capability provides sensory input (Camera, Microphone, GPS)."""
        return self in (Capability.CAMERA, Capability.MICROPHONE, Capability.GPS)


class RuntimeState(str, Enum):
    """
    Operational health state rating for edge device execution.
    """

    STARTING = "STARTING"
    READY = "READY"
    DEGRADED = "DEGRADED"
    LOW_POWER = "LOW_POWER"
    OFFLINE = "OFFLINE"
    SHUTDOWN = "SHUTDOWN"

    def is_operational(self) -> bool:
        """Return True if runtime state allows active cognitive execution."""
        return self in (RuntimeState.READY, RuntimeState.DEGRADED, RuntimeState.LOW_POWER, RuntimeState.OFFLINE)

    def requires_resource_preservation(self) -> bool:
        """Return True if runtime state mandates resource conservation policies."""
        return self in (RuntimeState.LOW_POWER, RuntimeState.DEGRADED)


@dataclass
class DeviceProfile:
    """
    Hardware-independent declarative description of a device deployment instance.
    """

    device_type: DeviceType
    capabilities: List[Capability] = field(default_factory=list)
    runtime_state: RuntimeState = RuntimeState.READY
    battery_level: float = 100.0
    available_storage: float = 1024.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    device_id: str = field(default_factory=lambda: f"dev-{uuid.uuid4().hex[:8]}")

    def has_capability(self, capability: Capability) -> bool:
        """Return True if profile supports specified capability."""
        return capability in self.capabilities

    def is_low_battery(self) -> bool:
        """Return True if battery level is below 20%."""
        return self.battery_level <= 20.0

    def is_storage_low(self) -> bool:
        """Return True if available storage is below 100 MB."""
        return self.available_storage <= 100.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize DeviceProfile to a dictionary representation."""
        return {
            "device_id": self.device_id,
            "device_type": self.device_type.value,
            "capabilities": [c.value for c in self.capabilities],
            "runtime_state": self.runtime_state.value,
            "battery_level": self.battery_level,
            "available_storage": self.available_storage,
            "metadata": dict(self.metadata),
        }


@dataclass
class EdgeSnapshot:
    """
    Point-in-time snapshot of registered edge devices, active capabilities, and checksum.
    """

    registered_devices_count: int
    active_profile_name: str
    current_runtime_state: RuntimeState
    available_capabilities_count: int
    checksum: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize EdgeSnapshot to a dictionary representation."""
        return {
            "timestamp": self.timestamp,
            "registered_devices_count": self.registered_devices_count,
            "active_profile_name": self.active_profile_name,
            "current_runtime_state": self.current_runtime_state.value,
            "available_capabilities_count": self.available_capabilities_count,
            "checksum": self.checksum,
        }
