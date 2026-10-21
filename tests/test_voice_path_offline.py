"""
Voice path without any device: audio-buffer handling, speech-recognition availability
reporting and runtime status. Nothing here opens a microphone, loads a speech model or
uses the network.
"""

from __future__ import annotations

import socket
import struct

import pytest

from src.perception import speech_recognition_engine as sre
from src.perception.voice_activity_detector import VoiceActivityDetector


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", lambda *a: pytest.fail("network used"))


def _tone(samples=800, amplitude=8000):
    return struct.pack(f"<{samples}h", *[(amplitude if i % 8 < 4 else -amplitude) for i in range(samples)])


@pytest.mark.parametrize("extra", [b"", b"\x01"])
def test_truncated_odd_length_audio_is_transcribed_not_crashed(extra):
    """Found in review: 321 bytes raised 'buffer size must be a multiple of element size'."""
    engine = sre.SpeechRecognitionEngine()
    engine._load_attempted = True               # no model: nothing is loaded
    result = engine.transcribe_segment(b"\x00" * 320 + extra)
    assert result.transcript == "" and result.confidence == 0.0


def test_speech_model_failure_yields_empty_transcript():
    class Broken:
        def transcribe(self, *a, **k):
            raise RuntimeError("model crashed")
    engine = sre.SpeechRecognitionEngine()
    engine.model = Broken()
    assert engine.transcribe_segment(_tone()).transcript == ""


def test_odd_length_chunk_with_speech_is_not_treated_as_silence():
    vad, odd = VoiceActivityDetector(), VoiceActivityDetector()
    even_result = vad.process_chunk(_tone())
    odd_result = odd.process_chunk(_tone() + b"\x01")
    assert odd_result.energy_rms == pytest.approx(even_result.energy_rms)
    assert odd_result.event_type == even_result.event_type


def test_availability_reports_missing_package(monkeypatch):
    monkeypatch.setattr(sre, "HAS_FASTER_WHISPER", False)
    usable, reason = sre.SpeechRecognitionEngine().availability()
    assert usable is False and "not installed" in reason


def test_availability_reports_load_failure_after_an_attempt(monkeypatch):
    import sys
    import types
    fake = types.ModuleType("faster_whisper")
    def no_model(*a, **k):
        raise FileNotFoundError("model files not found locally")
    fake.WhisperModel = no_model
    monkeypatch.setitem(sys.modules, "faster_whisper", fake)
    monkeypatch.setattr(sre, "HAS_FASTER_WHISPER", True)
    engine = sre.SpeechRecognitionEngine()
    assert engine.transcribe_segment(_tone()).transcript == ""
    usable, reason = engine.availability()
    assert usable is False and "not available locally" in reason and "MEMORA_ALLOW_MODEL_DOWNLOAD" in reason


def test_availability_states_that_downloads_are_off_by_default(monkeypatch):
    monkeypatch.setattr(sre, "HAS_FASTER_WHISPER", True)
    monkeypatch.delenv("MEMORA_ALLOW_MODEL_DOWNLOAD", raising=False)
    usable, reason = sre.SpeechRecognitionEngine().availability()
    assert usable and "must already be on this computer" in reason


def test_runtime_status_reports_speech_recognition_with_a_real_microphone(monkeypatch):
    from src.application.factory import build_application
    from src.memory.database import MemoraDatabase
    from src.runtime.runtime import AnchorRuntime
    coord = build_application(live_hardware=False, database=MemoraDatabase(":memory:"))
    assert AnchorRuntime(coord).get_subsystem_statuses()["Speech Recognition"].startswith("WARNING (Simulated")

    class RealLookingMic:            # stands in for a hardware adapter without opening anything
        def get_status(self):
            from src.runtime.runtime_models import DeviceStatus
            return DeviceStatus.HEALTHY
    coord.pipeline.runtime_manager.microphone = RealLookingMic()
    monkeypatch.setattr(sre, "HAS_FASTER_WHISPER", False)
    status = AnchorRuntime(coord).get_subsystem_statuses()["Speech Recognition"]
    assert status.startswith("FAILED (speech-to-text is not installed")
