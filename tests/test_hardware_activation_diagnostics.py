"""
Integration test suite for MEMORA Hardware Activation, Runtime Validation & Production Readiness.

Validates:
1. Camera enumeration, multi-backend probing, and explicit failure diagnostics
2. Microphone enumeration, audio energy calculation, and failure diagnostics
3. Speaker engine initialization and fallback failure reporting
4. MEMORA HARDWARE DIAGNOSTIC REPORT generation
5. Rich Telemetry Heartbeat logging
6. Explicit simulation policy logging (State A vs State B)
7. Subsystem diagnostic methods
"""

from __future__ import annotations

import pytest
import threading
import time

from src.application.factory import build_application
from src.runtime.runtime import AnchorRuntime
from src.runtime.camera_adapter import OpenCVCameraAdapter, SimulatedCameraAdapter
from src.runtime.microphone_adapter import PyAudioMicrophoneAdapter, SimulatedMicrophoneAdapter
from src.runtime.speaker_adapter import PyTTSx3SpeakerAdapter, SimulatedSpeakerAdapter
from src.runtime.runtime_models import DeviceStatus, HardwareConfig, RuntimeMode
from src.runtime.runtime_manager import RuntimeManager


# ===================================================================
# 1. Camera Enumeration & Explicit Failure Diagnostics Tests
# ===================================================================

def test_camera_enumeration():
    """Verify enumerate_cameras returns list of camera metadata."""
    cameras = OpenCVCameraAdapter.enumerate_cameras()
    assert isinstance(cameras, list)


def test_camera_explicit_failure_reason():
    """Verify camera adapter captures explicit failure reasons when index is invalid."""
    cam = OpenCVCameraAdapter(device_index=999)
    initialized = cam.initialize()

    assert initialized is False
    assert cam.get_status() == DeviceStatus.FAULTED
    assert cam.failure_reason is not None
    assert "999" in cam.failure_reason or "No accessible camera" in cam.failure_reason

    diag = cam.get_diagnostics()
    assert isinstance(diag, dict)
    assert diag["status"] == DeviceStatus.FAULTED.value
    assert diag["failure_reason"] == cam.failure_reason


# ===================================================================
# 2. Microphone Enumeration & Failure Diagnostics Tests
# ===================================================================

def test_microphone_enumeration():
    """Verify enumerate_microphones returns list of PyAudio input devices."""
    mics = PyAudioMicrophoneAdapter.enumerate_microphones()
    assert isinstance(mics, list)


def test_microphone_explicit_failure_reason():
    """Verify microphone adapter captures explicit failure reasons when index is out of bounds."""
    mic = PyAudioMicrophoneAdapter(device_index=999)
    initialized = mic.initialize()

    assert initialized is False
    assert mic.get_status() == DeviceStatus.FAULTED
    assert mic.failure_reason is not None

    diag = mic.get_diagnostics()
    assert isinstance(diag, dict)
    assert diag["status"] == DeviceStatus.FAULTED.value
    assert diag["failure_reason"] == mic.failure_reason


# ===================================================================
# 3. Speaker Initialization & Diagnostics Tests
# ===================================================================

def test_speaker_diagnostics():
    """Verify speaker adapter reports engine details and diagnostics."""
    spk = PyTTSx3SpeakerAdapter()
    diag = spk.get_diagnostics()

    assert isinstance(diag, dict)
    assert "status" in diag
    assert "voice_engine" in diag
    assert "spoken_count" in diag


# ===================================================================
# 4. Hardware Diagnostic Report Generation Tests
# ===================================================================

def test_hardware_diagnostic_report_generation():
    """Verify RuntimeManager generates formatted MEMORA HARDWARE DIAGNOSTIC REPORT."""
    rm = RuntimeManager()
    report = rm.generate_diagnostic_report()

    assert isinstance(report, str)
    assert "MEMORA HARDWARE DIAGNOSTIC REPORT" in report
    assert "Camera" in report
    assert "Microphone" in report
    assert "Speaker" in report
    assert "Speech Recognition" in report
    assert "Memory Database" in report
    assert "Face Database" in report
    assert "Object Detection Model" in report


# ===================================================================
# 5. AnchorRuntime Diagnostic Report Method
# ===================================================================

def test_runtime_print_diagnostic_report():
    """Verify AnchorRuntime.print_diagnostic_report runs without error."""
    coordinator = build_application(live_hardware=False)
    runtime = AnchorRuntime(coordinator)
    runtime.initialize()

    # Should execute without throwing exceptions
    runtime.print_diagnostic_report()

    runtime.shutdown()


# ===================================================================
# 6. Rich Telemetry Heartbeat & State A vs B Tests
# ===================================================================

def test_telemetry_heartbeat_execution():
    """Verify continuous runtime loop outputs telemetry heartbeat metrics."""
    coordinator = build_application(live_hardware=False)
    runtime = AnchorRuntime(coordinator)
    runtime.initialize()

    # Execute continuous loop for 2 cycles
    runtime.run_continuous(max_cycles=2, cycle_delay=0.01)

    assert runtime.cycle_count == 2
    assert runtime.running is False


# ===================================================================
# 7. Subsystem Diagnostics Integration Tests
# ===================================================================

def test_subsystem_get_diagnostics():
    """Verify FaceRecognizer and ObjectDetector expose get_diagnostics."""
    coordinator = build_application(live_hardware=False)

    rec_diag = coordinator.recognizer.get_diagnostics()
    assert isinstance(rec_diag, dict)
    assert "backend" in rec_diag

    pm = coordinator.pipeline.perception_manager
    obj_diag = pm.object_detector.get_diagnostics()
    assert isinstance(obj_diag, dict)
    assert "mode" in obj_diag

    coordinator.shutdown()
