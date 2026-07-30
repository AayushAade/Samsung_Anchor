"""
Comprehensive Test Suite for MEMORA Phase 39 — Edge Runtime & Device Integration Framework.

Tests:
1. Edge Data Models (Serialization of DeviceProfile, EdgeSnapshot, DeviceType, Capability, RuntimeState)
2. Device Registry (Deterministic device profile registration, removal, retrieval)
3. Capability Manager (Enabling/disabling abstract capabilities, checking capability flags)
4. Runtime Monitor (Evaluating health state based on battery, storage, and offline status)
5. Deployment Profiles (Activating SMARTPHONE, SMARTWATCH, SMART_GLASSES, OFFLINE_CLINICAL profiles)
6. Resource Manager (Deterministic low battery and storage pressure policy enforcement)
7. Central Edge Engine (Public façade register_device, activate_profile, evaluate_runtime, snapshot, explain)
8. Edge Explainer (Deterministic Markdown diagnostic report generation)
"""

import pytest
from src.edge import (
    DEPLOYMENT_PROFILES,
    Capability,
    CapabilityManager,
    DeploymentProfileManager,
    DeviceProfile,
    DeviceRegistry,
    DeviceType,
    EdgeEngine,
    EdgeExplainer,
    EdgeSnapshot,
    ResourceManager,
    RuntimeMonitor,
    RuntimeState,
)


# ======================================================================
# 1. Edge Data Models Tests
# ======================================================================

class TestEdgeModels:
    def test_device_profile_serialization(self):
        profile = DeviceProfile(
            device_type=DeviceType.SMARTWATCH,
            capabilities=[Capability.MICROPHONE, Capability.SPEAKER, Capability.HAPTIC],
            battery_level=85.0,
            available_storage=512.0,
        )
        d = profile.to_dict()
        assert d["device_type"] == "SMARTWATCH"
        assert "MICROPHONE" in d["capabilities"]
        assert profile.is_low_battery() is False
        assert profile.device_type.is_wearable() is True

    def test_edge_snapshot_serialization(self):
        snap = EdgeSnapshot(
            registered_devices_count=2,
            active_profile_name="SMARTWATCH",
            current_runtime_state=RuntimeState.READY,
            available_capabilities_count=5,
            checksum="abc12345",
        )
        d = snap.to_dict()
        assert d["registered_devices_count"] == 2
        assert d["current_runtime_state"] == "READY"


# ======================================================================
# 2. Device Registry Tests
# ======================================================================

class TestDeviceRegistry:
    def test_register_and_retrieve_device(self):
        registry = DeviceRegistry()
        profile = registry.register_device(
            device_type=DeviceType.SMART_GLASSES,
            capabilities=[Capability.CAMERA, Capability.DISPLAY],
            device_id="glasses-01",
        )
        assert registry.get_device_count() == 1
        assert registry.get_device("glasses-01") is not None
        assert registry.remove_device("glasses-01") is True
        assert registry.get_device_count() == 0


# ======================================================================
# 3. Capability Manager Tests
# ======================================================================

class TestCapabilityManager:
    def test_capability_enable_disable(self):
        mgr = CapabilityManager()
        mgr.set_active_capabilities([Capability.CAMERA, Capability.MICROPHONE])

        assert mgr.is_available(Capability.CAMERA) is True
        assert mgr.is_available(Capability.GPS) is False

        mgr.enable_capability(Capability.GPS)
        assert mgr.is_available(Capability.GPS) is True

        mgr.disable_capability(Capability.CAMERA)
        assert mgr.is_available(Capability.CAMERA) is False


# ======================================================================
# 4. Runtime Monitor Tests
# ======================================================================

class TestRuntimeMonitor:
    def test_evaluate_health(self):
        monitor = RuntimeMonitor()
        profile_ready = DeviceProfile(
            device_type=DeviceType.PHONE,
            capabilities=[Capability.NETWORK],
            battery_level=90.0,
            available_storage=1000.0,
        )
        state_ready = monitor.evaluate_health(profile_ready, network_available=True)
        assert state_ready == RuntimeState.READY

        profile_low_battery = DeviceProfile(
            device_type=DeviceType.PHONE,
            capabilities=[Capability.NETWORK],
            battery_level=5.0,
            available_storage=1000.0,
        )
        state_low = monitor.evaluate_health(profile_low_battery, network_available=True)
        assert state_low == RuntimeState.LOW_POWER
        assert monitor.has_warnings() is True


# ======================================================================
# 5. Deployment Profiles Tests
# ======================================================================

class TestDeploymentProfiles:
    def test_profile_retrieval(self):
        caps_phone = DeploymentProfileManager.get_profile("SMARTPHONE")
        assert Capability.CAMERA in caps_phone

        caps_watch = DeploymentProfileManager.get_profile("SMARTWATCH")
        assert Capability.HAPTIC in caps_watch
        assert Capability.CAMERA not in caps_watch

        assert DeploymentProfileManager.has_vision("SMART_GLASSES") is True
        assert DeploymentProfileManager.has_haptic("SMARTWATCH") is True


# ======================================================================
# 6. Resource Manager Tests
# ======================================================================

class TestResourceManager:
    def test_resource_policy_evaluation(self):
        mgr = ResourceManager()
        actions = mgr.evaluate_resource_policies(battery_level=8.0, available_storage_mb=30.0)
        assert len(actions) >= 2
        assert any("Critical battery" in a for a in actions)
        assert any("Critical storage" in a for a in actions)


# ======================================================================
# 7. Central Edge Engine Tests
# ======================================================================

class TestEdgeEngine:
    def test_engine_register_and_activate(self):
        engine = EdgeEngine()
        dev = engine.register_device(
            device_type=DeviceType.SMARTWATCH,
            capabilities=DeploymentProfileManager.get_profile("SMARTWATCH"),
            device_id="watch-001",
        )
        assert dev.device_id == "watch-001"

        caps = engine.activate_profile("SMART_GLASSES")
        assert Capability.CAMERA in caps
        assert engine.get_active_profile_name() == "SMART_GLASSES"

        snap = engine.snapshot()
        assert snap.active_profile_name == "SMART_GLASSES"

        exp_str = engine.explain()
        assert "Edge Runtime Status" in exp_str


# ======================================================================
# 8. Edge Explainer Tests
# ======================================================================

class TestEdgeExplainer:
    def test_explain_engine_state(self):
        engine = EdgeEngine()
        engine.activate_profile("OFFLINE_CLINICAL")

        markdown = EdgeExplainer.explain_engine_state(engine)
        assert "MEMORA Edge Runtime & Device Integration Diagnostic Report" in markdown
        assert "Active Deployment Profile" in markdown
        assert "Active Capability Matrix" in markdown
