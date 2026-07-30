"""
MEMORA Edge Device Registry.

Maintains a thread-safe registry of hardware device profiles without physical device discovery,
Bluetooth scanning, USB polling, or platform SDK dependencies.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from src.edge.edge_models import Capability, DeviceProfile, DeviceType, RuntimeState


class DeviceRegistry:
    """
    Thread-safe registry for managing abstract DeviceProfile instances.
    Enforces deterministic registration and query interfaces.
    """

    def __init__(self) -> None:
        self._devices: Dict[str, DeviceProfile] = {}
        self._lock = threading.Lock()

    def register_device(
        self,
        device_type: DeviceType,
        capabilities: List[Capability],
        battery_level: float = 100.0,
        available_storage: float = 1024.0,
        device_id: Optional[str] = None,
    ) -> DeviceProfile:
        """
        Register a hardware device profile deterministically.
        """
        profile = DeviceProfile(
            device_type=device_type,
            capabilities=list(capabilities),
            battery_level=battery_level,
            available_storage=available_storage,
        )
        if device_id:
            profile.device_id = device_id

        with self._lock:
            self._devices[profile.device_id] = profile
            return profile

    def remove_device(self, device_id: str) -> bool:
        """
        Remove a device profile from registry.
        """
        with self._lock:
            if device_id in self._devices:
                del self._devices[device_id]
                return True
            return False

    def get_device(self, device_id: str) -> Optional[DeviceProfile]:
        """
        Retrieve a registered device profile by ID.
        """
        with self._lock:
            return self._devices.get(device_id)

    def list_devices(self) -> List[DeviceProfile]:
        """
        Return all registered device profiles.
        """
        with self._lock:
            return list(self._devices.values())

    def get_devices_by_type(self, device_type: DeviceType) -> List[DeviceProfile]:
        """
        Return registered devices matching specified DeviceType.
        """
        with self._lock:
            return [d for d in self._devices.values() if d.device_type == device_type]

    def get_wearable_devices(self) -> List[DeviceProfile]:
        """
        Return registered wearable devices (Smartwatch, Smart Glasses).
        """
        with self._lock:
            return [d for d in self._devices.values() if d.device_type.is_wearable()]

    def get_device_count(self) -> int:
        """Return total number of registered devices."""
        with self._lock:
            return len(self._devices)

    def clear(self) -> None:
        """
        Clear all registered devices.
        """
        with self._lock:
            self._devices.clear()
