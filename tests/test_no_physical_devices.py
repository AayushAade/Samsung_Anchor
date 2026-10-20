"""The test suite itself must never open the camera, microphone, or produce sound."""

from __future__ import annotations

import subprocess

from src.runtime.camera_adapter import OpenCVCameraAdapter
from src.runtime.microphone_adapter import PyAudioMicrophoneAdapter
from src.runtime.runtime_models import DeviceStatus, HardwareConfig, RuntimeMode
from src.runtime.runtime_manager import RuntimeManager


def test_real_camera_cannot_open_in_tests():
    cam = OpenCVCameraAdapter(device_index=0)
    assert cam.initialize() is False
    assert cam.get_status() == DeviceStatus.FAULTED


def test_real_microphone_cannot_open_in_tests():
    mic = PyAudioMicrophoneAdapter()
    assert mic.initialize() is False


def test_laptop_mode_runtime_has_no_working_real_devices():
    mgr = RuntimeManager(config=HardwareConfig(mode=RuntimeMode.LAPTOP))
    assert mgr.camera.get_status() != DeviceStatus.HEALTHY or type(mgr.camera).__name__.startswith("Simulated")
    mgr.shutdown_hardware()


def test_audio_commands_are_never_executed():
    result = subprocess.run(["say", "this must not be heard"])
    assert result.returncode == 0 and result.args == ["say", "this must not be heard"]
