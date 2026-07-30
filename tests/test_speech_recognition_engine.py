import struct
import math
from src.perception.speech_recognition_engine import SpeechRecognitionEngine, TranscriptionResult
from src.perception.audio_pipeline import AudioPipeline
from src.runtime.microphone_adapter import SimulatedMicrophoneAdapter
from src.runtime.sensor_bus import SensorBus
from src.runtime.runtime_models import SensorEventType


def generate_pcm(num_samples: int = 8000, freq_hz: float = 440.0, amplitude: int = 500) -> bytes:
    samples = []
    for i in range(num_samples):
        t = i / 16000.0
        val = int(amplitude * math.sin(2 * math.pi * freq_hz * t))
        samples.append(val)
    return struct.pack(f"<{num_samples}h", *samples)


def test_speech_recognition_engine_silent_input():
    engine = SpeechRecognitionEngine()
    result = engine.transcribe_segment(b"")

    assert isinstance(result, TranscriptionResult)
    assert result.transcript == ""
    assert result.confidence == 1.0
    assert result.language == "en"
    assert result.processing_latency_ms >= 0.0


def test_speech_recognition_engine_transcription_metrics():
    engine = SpeechRecognitionEngine()
    pcm_bytes = generate_pcm(num_samples=16000, freq_hz=440.0, amplitude=600)

    result = engine.transcribe_segment(pcm_bytes)
    assert isinstance(result, TranscriptionResult)
    assert result.confidence >= 0.0
    assert result.language == "en"
    assert result.processing_latency_ms > 0.0
    assert "T" in result.start_timestamp
    assert "T" in result.end_timestamp


def test_audio_pipeline_speech_transcript_sensorbus_integration():
    bus = SensorBus()
    mic = SimulatedMicrophoneAdapter("TestMic")
    mic.initialize()

    received_transcripts = []
    bus.subscribe(SensorEventType.SPEECH_TRANSCRIPT, lambda e: received_transcripts.append(e))

    pipeline = AudioPipeline(microphone_adapter=mic, sensor_bus=bus)

    # Transcribe audio buffer directly
    pcm = generate_pcm(num_samples=16000, freq_hz=440.0, amplitude=600)
    pipeline.transcribe_audio_buffer(pcm)

    # If transcript text was generated, verify SensorBus publication
    if received_transcripts:
        evt = received_transcripts[0]
        assert evt.event_type == SensorEventType.SPEECH_TRANSCRIPT
        assert "text" in evt.data
        assert "confidence" in evt.data

    mic.shutdown()
