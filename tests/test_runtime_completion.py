"""
Unit tests verifying continuous execution, subsystem observability, and hardware resilience.
"""

from unittest.mock import MagicMock
import pytest

from src.application.factory import build_application
from src.runtime.runtime import AnchorRuntime
from src.runtime.camera_adapter import SimulatedCameraAdapter


def test_build_application_defaults():
    """Verify build_application creates a coordinator with default subsystems when parameters are None."""
    coordinator = build_application()
    assert coordinator is not None
    assert coordinator.database is not None
    assert coordinator.recognizer is not None
    assert coordinator.listener is not None
    assert coordinator.binder is not None
    assert coordinator.speaker is not None


def test_runtime_subsystem_statuses():
    """Verify Phase 6 observability statuses map."""
    coordinator = build_application()
    runtime = AnchorRuntime(coordinator)
    runtime.initialize()

    statuses = runtime.get_subsystem_statuses()
    assert isinstance(statuses, dict)
    assert "Runtime" in statuses
    assert "Camera" in statuses
    assert "Audio" in statuses
    assert "Memory" in statuses
    assert "Perception" in statuses
    assert "Cognition" in statuses
    assert "Care Policy" in statuses
    assert "Decision Trace" in statuses
    assert "Speaker" in statuses
    assert statuses["Runtime"] == "READY"


def test_simulated_camera_adapter_read():
    """Verify SimulatedCameraAdapter exposes a working read() method matching OpenCV interface."""
    adapter = SimulatedCameraAdapter("Test_Cam")
    adapter.initialize()

    success, frame = adapter.read()
    assert success is True
    assert isinstance(frame, dict)
    assert frame["device"] == "Test_Cam"


def test_runtime_run_continuous_max_cycles():
    """Verify run_continuous runs specified max_cycles and shuts down gracefully."""
    coordinator = build_application()
    runtime = AnchorRuntime(coordinator)

    runtime.run_continuous(max_cycles=3, cycle_delay=0.01)

    assert runtime.cycle_count == 3
    assert runtime.running is False
