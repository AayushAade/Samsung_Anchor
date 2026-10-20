"""
Recording the microphone for Google's online transcription must never happen
silently: it needs MEMORA_ALLOW_CLOUD_ASR=1, and identity learning needs
voice-recording consent.
"""

from __future__ import annotations

import pytest

from src.audio import audio_listener
from src.audio.audio_listener import MemoraAudioListener
from src.application.factory import build_application
from src.clinical.clinical_models import ConsentFeature
from src.memory.database import MemoraDatabase


class _ExplodingMicrophone:
    def __init__(self, *a, **k):
        raise AssertionError("microphone must not be opened")


@pytest.mark.skipif(not audio_listener.HAS_SPEECH_RECOGNITION, reason="SpeechRecognition not installed")
def test_no_recording_without_cloud_asr_opt_in(monkeypatch):
    monkeypatch.delenv("MEMORA_ALLOW_CLOUD_ASR", raising=False)
    monkeypatch.setattr(audio_listener.sr, "Microphone", _ExplodingMicrophone)
    listener = MemoraAudioListener(mock_mode=False, device_index=0)
    assert listener.listen_and_transcribe() is None   # falls back to typing; no tty in tests
    assert listener.mock_mode is True


def test_listener_works_without_speech_recognition_package(monkeypatch):
    monkeypatch.setattr(audio_listener, "HAS_SPEECH_RECOGNITION", False)
    listener = MemoraAudioListener(mock_mode=False)
    assert listener.mock_mode is True and listener.recognizer is None


def test_identity_learning_requires_voice_consent_for_real_microphone():
    coord = build_application(live_hardware=False, database=MemoraDatabase(":memory:"))
    coord.listener.mock_mode = False              # pretend a real microphone is in use
    assert coord.start_identity_learning("face_1") is False
    coord.pipeline.consent_mgr.update_consent(ConsentFeature.VOICE_RECORDING, True)
    coord.listener.mock_mode = True               # keep the test from listening at all
    assert coord.start_identity_learning("face_1") is True


def test_diagnostics_disclose_cloud_transcription(monkeypatch):
    coord = build_application(live_hardware=False, database=MemoraDatabase(":memory:"))
    monkeypatch.delenv("MEMORA_ALLOW_CLOUD_ASR", raising=False)
    assert "online service disabled" in coord.pipeline.runtime_manager.generate_diagnostic_report()
    monkeypatch.setenv("MEMORA_ALLOW_CLOUD_ASR", "1")
    assert "audio leaves this device" in coord.pipeline.runtime_manager.generate_diagnostic_report()
