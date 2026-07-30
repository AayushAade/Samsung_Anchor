"""
MEMORA Central Edge Engine.

Public façade coordinating DeviceRegistry, CapabilityManager, RuntimeMonitor,
DeploymentProfileManager, and ResourceManager into a unified edge orchestration interface.
"""

from __future__ import annotations

import hashlib
import json
import threading
from typing import Any, Dict, List, Optional

from src.edge.capability_manager import CapabilityManager
from src.edge.deployment_profile import DeploymentProfileManager
from src.edge.device_registry import DeviceRegistry
from src.edge.edge_models import Capability, DeviceProfile, DeviceType, EdgeSnapshot, RuntimeState
from src.edge.resource_manager import ResourceManager
from src.edge.runtime_monitor import RuntimeMonitor


class EdgeEngine:
    """
    Unified public façade for Edge Runtime & Device Integration Framework.
    Manages device registration, deployment profile activation, runtime health evaluation,
    and resource policy enforcement without platform SDK dependencies.
    """

    def __init__(self) -> None:
        self.registry = DeviceRegistry()
        self.capability_manager = CapabilityManager()
        self.runtime_monitor = RuntimeMonitor()
        self.resource_manager = ResourceManager()

        self._active_profile_name = "SMARTPHONE"
        self._lock = threading.Lock()

        # Register default device profile
        self.register_device(
            device_type=DeviceType.PHONE,
            capabilities=DeploymentProfileManager.get_profile("SMARTPHONE"),
            battery_level=100.0,
            available_storage=2048.0,
            device_id="dev-default-phone",
        )

    def register_device(
        self,
        device_type: DeviceType,
        capabilities: List[Capability],
        battery_level: float = 100.0,
        available_storage: float = 1024.0,
        device_id: Optional[str] = None,
    ) -> DeviceProfile:
        """
        Register a device profile and update active capabilities.
        """
        profile = self.registry.register_device(
            device_type=device_type,
            capabilities=capabilities,
            battery_level=battery_level,
            available_storage=available_storage,
            device_id=device_id,
        )
        self.capability_manager.set_active_capabilities(profile.capabilities)
        return profile

    def activate_profile(self, profile_name: str) -> List[Capability]:
        """
        Activate a pre-configured deployment profile (SMARTPHONE, SMARTWATCH, SMART_GLASSES, OFFLINE_CLINICAL).
        """
        caps = DeploymentProfileManager.get_profile(profile_name)
        self.capability_manager.set_active_capabilities(caps)
        with self._lock:
            self._active_profile_name = profile_name.upper()
            return caps

    def evaluate_runtime(self, device_id: Optional[str] = None) -> RuntimeState:
        """
        Evaluate runtime health and resource policies for specified or default device.
        """
        profile = None
        if device_id:
            profile = self.registry.get_device(device_id)
        if not profile:
            devices = self.registry.list_devices()
            profile = devices[0] if devices else DeviceProfile(device_type=DeviceType.PHONE)

        is_network = Capability.NETWORK in self.capability_manager.get_active_capabilities()
        state = self.runtime_monitor.evaluate_health(profile, network_available=is_network)
        self.resource_manager.evaluate_resource_policies(profile.battery_level, profile.available_storage)
        return state

    def get_active_profile_name(self) -> str:
        """Return currently active deployment profile name."""
        with self._lock:
            return self._active_profile_name

    def is_capability_supported(self, capability: Capability) -> bool:
        """Check if an abstract capability is currently supported by the active engine profile."""
        return self.capability_manager.is_available(capability)

    def get_registered_device_count(self) -> int:
        """Return count of currently registered devices in registry."""
        return self.registry.get_device_count()

    def get_active_capability_count(self) -> int:
        """Return count of active capabilities in capability manager."""
        return len(self.capability_manager.get_active_capabilities())

    def explain(self) -> str:
        """
        Return human-readable diagnostic explanation of edge runtime state.
        """
        devices = self.registry.list_devices()
        active_caps = self.capability_manager.get_active_capabilities()
        state = self.evaluate_runtime()
        warnings = self.runtime_monitor.get_warnings()

        return (
            f"Edge Runtime Status [{state.value}]\n"
            f"Active Deployment Profile: `{self._active_profile_name}` | Registered Devices: {len(devices)}\n"
            f"Active Capabilities ({len(active_caps)}): {', '.join([c.value for c in active_caps])}\n"
            f"Active Warnings: {'; '.join(warnings) if warnings else 'None'}"
        )

    def compute_checksum(self) -> str:
        """Compute SHA256 checksum across registered devices and active capability states."""
        with self._lock:
            data = {
                "devices": len(self.registry.list_devices()),
                "profile": self._active_profile_name,
                "caps": len(self.capability_manager.get_active_capabilities()),
            }
            raw = json.dumps(data, sort_keys=True).encode("utf-8")
            return hashlib.sha256(raw).hexdigest()[:16]

    def snapshot(self) -> EdgeSnapshot:
        """Generate a point-in-time EdgeSnapshot object."""
        devices = self.registry.list_devices()
        active_caps = self.capability_manager.get_active_capabilities()
        state = self.evaluate_runtime()

        with self._lock:
            chk = self.compute_checksum()
            return EdgeSnapshot(
                registered_devices_count=len(devices),
                active_profile_name=self._active_profile_name,
                current_runtime_state=state,
                available_capabilities_count=len(active_caps),
                checksum=chk,
            )

    def reset(self) -> None:
        """Reset edge registry, capability manager, runtime monitor, and resource manager."""
        with self._lock:
            self.registry.clear()
            self.capability_manager.clear()
            self.runtime_monitor.clear()
            self.resource_manager.clear()
            self._active_profile_name = "SMARTPHONE"
