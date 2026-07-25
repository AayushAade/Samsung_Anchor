import struct
import math
from src.perception.voice_activity_detector import VoiceActivityDetector, VADResult
from src.perception.sensor_models import AudioEventType
from src.perception.audio_pipeline import AudioPipeline
from src.runtime.microphone_adapter import SimulatedMicrophoneAdapter
from src.runtime.sensor_bus import SensorBus
from src.runtime.runtime_models import SensorEventType


def generate_pcm_chunk(amplitude: int = 0, num_samples: int = 1024, freq_hz: float = 440.0, sample_rate: int = 16000) -> bytes:
    if amplitude == 0:
        return b"\x00" * (num_samples * 2)

    samples = []
    for i in range(num_samples):
        t = i / float(sample_rate)
        val = int(amplitude * math.sin(2 * math.pi * freq_hz * t))
        samples.append(val)

    return struct.pack(f"<{num_samples}h", *samples)


def test_vad_continuous_silence():
    vad = VoiceActivityDetector(energy_threshold=45.0)
    silence_pcm = generate_pcm_chunk(amplitude=0)

    res = vad.process_chunk(silence_pcm)
    assert res.is_speech is False
    assert res.event_type == AudioEventType.SILENCE
    assert res.speech_duration == 0.0
    assert res.energy_rms == 0.0


def test_vad_continuous_speech():
    vad = VoiceActivityDetector(energy_threshold=45.0)
    speech_pcm = generate_pcm_chunk(amplitude=500, freq_hz=440.0)

    # Process 3 consecutive speech chunks
    for i in range(1, 4):
        res = vad.process_chunk(speech_pcm)
        assert res.is_speech is True
        assert res.event_type == AudioEventType.SPEECH_PRESENT
        assert res.confidence >= 0.60
        assert res.speech_duration > 0.0


def test_vad_speech_followed_by_silence():
    vad = VoiceActivityDetector(energy_threshold=45.0)
    speech_pcm = generate_pcm_chunk(amplitude=600)
    silence_pcm = generate_pcm_chunk(amplitude=0)

    # Speech chunk
    res_speech = vad.process_chunk(speech_pcm)
    assert res_speech.is_speech is True

    # Transition to silence
    res_silence = vad.process_chunk(silence_pcm)
    assert res_silence.is_speech is False
    assert res_silence.event_type == AudioEventType.SILENCE
    assert res_silence.speech_duration == 0.0


def test_vad_short_noise_burst():
    vad = VoiceActivityDetector(energy_threshold=45.0)
    burst_pcm = generate_pcm_chunk(amplitude=700, num_samples=1024)

    res = vad.process_chunk(burst_pcm)
    assert res.energy_rms > vad.energy_threshold
    assert res.confidence > 0.50


def test_audio_pipeline_vad_sensorbus_integration():
    bus = SensorBus()
    mic = SimulatedMicrophoneAdapter("TestMic")
    mic.initialize()

    received_events = []
    bus.subscribe(SensorEventType.AUDIO_EVENT, lambda e: received_events.append(e))

    pipeline = AudioPipeline(microphone_adapter=mic, sensor_bus=bus)
    chunk_data = pipeline.process_audio_chunk()

    assert chunk_data is not None
    assert "vad" in chunk_data
    assert "is_speech" in chunk_data["vad"]
    assert len(received_events) == 1
    assert received_events[0].data["vad"]["event_type"] in ["Silence", "Speech Present"]
    mic.shutdown()
