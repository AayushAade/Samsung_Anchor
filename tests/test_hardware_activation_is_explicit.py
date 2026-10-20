"""
Real hardware can only be activated explicitly (live_hardware=True, i.e. the
--live-hardware flag). Environment variables such as MEMORA_PROFILE must never
turn text chat, simulation, or the default runtime into hardware operation.
(The suite-wide device guard in conftest.py is a second line of defence; these
tests check which adapter classes are constructed.)
"""

from __future__ import annotations

import pytest

from src.application.factory import build_application, hardware_config_for
from src.memory.database import MemoraDatabase
from src.runtime.runtime_models import RuntimeMode

HARDWARE_PROFILES = ["LAPTOP", "DEV", "PRODUCTION", "RASPBERRY_PI", "JETSON"]


def _adapter_classes(coord):
    rm = coord.pipeline.runtime_manager
    return {type(rm.camera).__name__, type(rm.microphone).__name__, type(rm.speaker).__name__}


@pytest.mark.parametrize("profile", HARDWARE_PROFILES)
@pytest.mark.parametrize("live_hardware", [False, None])
def test_profile_env_cannot_enable_hardware(monkeypatch, profile, live_hardware):
    monkeypatch.setenv("MEMORA_PROFILE", profile)
    coord = build_application(live_hardware=live_hardware, database=MemoraDatabase(":memory:"))
    assert coord.pipeline.runtime_manager.config.mode == RuntimeMode.SIMULATION
    assert _adapter_classes(coord) == {"SimulatedCameraAdapter", "SimulatedMicrophoneAdapter", "SimulatedSpeakerAdapter"}
    assert coord.listener.mock_mode is True and coord.recognizer.mock_mode is True


@pytest.mark.parametrize("profile", HARDWARE_PROFILES)
def test_simulation_journeys_and_chat_stay_simulated(monkeypatch, profile):
    monkeypatch.setenv("MEMORA_PROFILE", profile)
    from src.simulation.journeys import Journey, JourneyContext
    ctx = JourneyContext(Journey("hw", "", []))
    try:
        assert _adapter_classes(ctx.session.coordinator) == {
            "SimulatedCameraAdapter", "SimulatedMicrophoneAdapter", "SimulatedSpeakerAdapter"}
    finally:
        ctx.close()


def test_explicit_activation_selects_hardware_mode(monkeypatch):
    monkeypatch.delenv("MEMORA_PROFILE", raising=False)
    assert hardware_config_for(True).mode == RuntimeMode.LAPTOP
    monkeypatch.setenv("MEMORA_PROFILE", "RASPBERRY_PI")
    assert hardware_config_for(True).mode == RuntimeMode.RASPBERRY_PI
    monkeypatch.setenv("MEMORA_PROFILE", "SIMULATION")
    assert hardware_config_for(True).mode == RuntimeMode.LAPTOP  # explicit request wins over a sim profile
    for value in (False, None):
        assert hardware_config_for(value).mode == RuntimeMode.SIMULATION


@pytest.mark.parametrize("profile", HARDWARE_PROFILES)
def test_direct_pipeline_construction_is_simulated(monkeypatch, profile):
    from src.pipeline.cognitive_pipeline import CognitivePipeline
    monkeypatch.setenv("MEMORA_PROFILE", profile)
    p = CognitivePipeline(MemoraDatabase(":memory:"))
    try:
        assert p.runtime_manager.config.mode == RuntimeMode.SIMULATION
    finally:
        p.shutdown()


@pytest.mark.parametrize("live_hardware", [False, None])
def test_vision_standalone_refuses_without_live_hardware(monkeypatch, live_hardware):
    """The standalone camera diagnostic must not open a device unless --live-hardware is given."""
    import cv2
    import app as memora_app
    opened = []
    monkeypatch.setattr(cv2, "VideoCapture", lambda *a, **k: opened.append(a) or pytest.fail("camera opened"))
    monkeypatch.setattr(memora_app, "run_vision_standalone_loop", lambda: opened.append("loop"))
    with pytest.raises(SystemExit) as exit_info:
        memora_app.main(vision_standalone=True, live_hardware=live_hardware)
    assert exit_info.value.code == 2 and opened == []
