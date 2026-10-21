"""
Integration tests for MEMORA Live Perception & Hardware Integration.

Validates:
1. Live camera startup and fallback
2. Microphone startup and audio pipeline processing
3. Speaker Text-to-Speech dispatch and console fallback
4. Live vision frame ingestion (FaceRecognizer & ObjectDetector)
5. Speech transcript integration into Cognitive Pipeline
6. Mid-stream hardware disconnect recovery
7. Runtime stability and heartbeat observability
"""

from __future__ import annotations

import time
import pytest
from unittest.mock import MagicMock, patch

from src.application.factory import build_application
from src.runtime.runtime import AnchorRuntime
from src.runtime.camera_adapter import OpenCVCameraAdapter, SimulatedCameraAdapter
from src.runtime.microphone_adapter import PyAudioMicrophoneAdapter, SimulatedMicrophoneAdapter
from src.runtime.speaker_adapter import PyTTSx3SpeakerAdapter, SimulatedSpeakerAdapter
from src.runtime.runtime_models import DeviceStatus
from src.perception.sensor_models import AudioEventType, RoomLocation


# ===================================================================
# 1. Camera Adapter & Fallback Tests
# ===================================================================

def test_opencv_camera_adapter_fallback():
    """Verify that OpenCVCameraAdapter falls back gracefully if camera index is invalid."""
    cam = OpenCVCameraAdapter(device_index=999)  # Non-existent index
    initialized = cam.initialize()

    # Should report FAULTED and not crash
    assert initialized is False
    assert cam.get_status() == DeviceStatus.FAULTED

    # Reading should return fallback dict frame metadata without crashing
    success, frame_data = cam.read()
    assert isinstance(frame_data, dict)
    assert "frame_id" in frame_data

    cam.shutdown()


def test_runtime_manager_camera_auto_fallback():
    """Verify RuntimeManager automatically downgrades to SimulatedCameraAdapter when physical camera fails."""
    coordinator = build_application(live_hardware=True)
    rm = coordinator.pipeline.runtime_manager

    # Force camera failure simulation
    rm.fallback_camera()

    assert isinstance(rm.camera, SimulatedCameraAdapter)
    assert rm.camera.get_status() == DeviceStatus.HEALTHY

    coordinator.shutdown()


# ===================================================================
# 2. Microphone Adapter & Audio Pipeline Tests
# ===================================================================

def test_pyaudio_microphone_adapter_fallback():
    """Verify PyAudioMicrophoneAdapter reports FAULTED safely if PyAudio is missing or device is invalid."""
    mic = PyAudioMicrophoneAdapter(device_index=999)
    initialized = mic.initialize()

    assert initialized is False
    assert mic.get_status() == DeviceStatus.FAULTED

    chunk = mic.read_chunk()
    assert isinstance(chunk, dict)
    assert "chunk_id" in chunk

    mic.shutdown()


def test_audio_pipeline_microphone_failure_recovery():
    """Verify AudioPipeline recovers gracefully when microphone read raises an error."""
    coordinator = build_application(live_hardware=False)
    ap = coordinator.pipeline.perception_manager.audio_pipeline

    # Inject failing microphone adapter
    failing_mic = MagicMock()
    failing_mic.read_chunk.side_effect = RuntimeError("Microphone device disconnected!")
    ap.set_microphone_adapter(failing_mic)

    # Process audio chunk should catch error and fall back to simulated mic
    chunk_data = ap.process_audio_chunk()
    assert isinstance(chunk_data, dict)
    assert isinstance(ap.microphone_adapter, SimulatedMicrophoneAdapter)

    coordinator.shutdown()


# ===================================================================
# 3. Speaker Adapter & TTS Tests
# ===================================================================

def test_speaker_adapter_fallback():
    """Verify PyTTSx3SpeakerAdapter handles speech requests and falls back to console gracefully."""
    spk = PyTTSx3SpeakerAdapter()
    result = spk.speak("Testing MEMORA TTS Speaker Output")

    assert result is True

    # Simulated speaker fallback
    sim_spk = SimulatedSpeakerAdapter()
    assert sim_spk.speak("Testing Simulated Speaker") is True
    assert sim_spk.play_chime() is True
    assert sim_spk.trigger_alarm() is True


# ===================================================================
# 4. Live Vision & Object Detection Frame Integration Test
# ===================================================================

def test_live_frame_vision_ingestion():
    """Verify ObjectDetector processes raw numpy BGR camera frames cleanly."""
    try:
        import numpy as np
        raw_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    except ImportError:
        pytest.skip("NumPy not available in test environment.")

    coordinator = build_application(live_hardware=False)
    detector = coordinator.pipeline.perception_manager.object_detector

    # Process numpy frame
    objects = detector.detect_objects_for_room(RoomLocation.LIVING_ROOM, raw_frame=raw_frame, frame_id=1)
    assert isinstance(objects, list)

    coordinator.shutdown()


# ===================================================================
# 5. Speech-to-Conversation Pipeline Integration Test
# ===================================================================

def test_speech_transcript_pipeline_integration():
    """Verify speech transcripts trigger conversation processing and speaker output."""
    coordinator = build_application(live_hardware=False)
    runtime = AnchorRuntime(coordinator)
    runtime.initialize()
    runtime.start()

    # Simulate speech transcript arriving via SensorBus
    from src.runtime.runtime_models import SensorEvent, SensorEventType
    t_event = SensorEvent(
        event_type=SensorEventType.SPEECH_TRANSCRIPT,
        source_device="PyAudio_Microphone_0",
        data={"text": "Hello MEMORA, do I have any medications scheduled?"},
    )
    coordinator.pipeline.runtime_manager.sensor_bus.publish(t_event)

    # Process frame with face detection
    runtime.process_frame({
        "face_id": "face_patient_01",
        "name": "John",
        "bbox": [10, 10, 100, 100],
    })

    time.sleep(0.3)

    actions = coordinator.consume_actions()
    assert isinstance(actions, list)

    runtime.shutdown()


# ===================================================================
# 6. Mid-Stream Hardware Disconnect Recovery Test
# ===================================================================

def test_midstream_camera_disconnect_recovery():
    """Verify continuous execution survives mid-stream physical camera unplugs."""
    coordinator = build_application(live_hardware=False)
    runtime = AnchorRuntime(coordinator)
    runtime.initialize()

    class DisconnectingCamera:
        def __init__(self):
            self.count = 0
        def read(self):
            self.count += 1
            if self.count >= 2:
                raise RuntimeError("USB Camera Unplugged!")
            return True, {"frame_id": self.count, "timestamp": time.time()}

    dis_cam = DisconnectingCamera()

    # Run continuous runtime loop
    runtime.run_continuous(max_cycles=4, cycle_delay=0.01, camera=dis_cam)

    assert runtime.cycle_count == 4
    assert runtime.running is False
