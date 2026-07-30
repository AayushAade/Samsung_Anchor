from dataclasses import dataclass, field
from datetime import datetime
import math
import struct
from typing import Dict, Any, Optional
from src.perception.sensor_models import AudioEventType


@dataclass
class VADResult:
    is_speech: bool
    event_type: AudioEventType
    confidence: float
    speech_duration: float
    energy_rms: float
    zcr: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class VoiceActivityDetector:
    """
    Production-grade, lightweight offline Voice Activity Detection (VAD) engine.
    Analyzes PCM audio buffers to classify SPEECH_PRESENT vs SILENCE in real time
    with sub-millisecond execution latency.
    """

    def __init__(
        self,
        energy_threshold: float = 45.0,
        zcr_threshold: float = 0.05,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
    ) -> None:
        self.energy_threshold = energy_threshold
        self.zcr_threshold = zcr_threshold
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size

        self.noise_floor = energy_threshold * 0.5
        self.contiguous_speech_chunks = 0
        self.chunk_duration_sec = chunk_size / float(sample_rate)

    def process_chunk(self, raw_audio: Optional[bytes]) -> VADResult:
        now_iso = datetime.now().isoformat()

        if not raw_audio or len(raw_audio) < 2:
            self.contiguous_speech_chunks = 0
            return VADResult(
                is_speech=False,
                event_type=AudioEventType.SILENCE,
                confidence=0.95,
                speech_duration=0.0,
                energy_rms=0.0,
                zcr=0.0,
                timestamp=now_iso,
            )

        num_samples = len(raw_audio) // 2
        try:
            samples = struct.unpack(f"<{num_samples}h", raw_audio)
        except Exception:
            samples = tuple()

        if not samples:
            self.contiguous_speech_chunks = 0
            return VADResult(
                is_speech=False,
                event_type=AudioEventType.SILENCE,
                confidence=0.95,
                speech_duration=0.0,
                energy_rms=0.0,
                zcr=0.0,
                timestamp=now_iso,
            )

        # 1. Compute RMS Energy
        sum_sq = sum(s * s for s in samples)
        rms = math.sqrt(sum_sq / len(samples))

        # 2. Compute Zero Crossing Rate (ZCR)
        zero_crossings = sum(
            1 for i in range(1, len(samples)) if (samples[i] >= 0 and samples[i - 1] < 0) or (samples[i] < 0 and samples[i - 1] >= 0)
        )
        zcr = zero_crossings / float(len(samples))

        # 3. Adaptive Noise Floor Update during silence
        if rms < self.energy_threshold:
            self.noise_floor = 0.95 * self.noise_floor + 0.05 * rms

        # 4. Speech Classification
        dynamic_threshold = max(self.energy_threshold, self.noise_floor * 2.5)
        is_speech = (rms > dynamic_threshold) and (zcr > 0.01)

        if is_speech:
            self.contiguous_speech_chunks += 1
            speech_dur = self.contiguous_speech_chunks * self.chunk_duration_sec
            snr = rms / (self.noise_floor + 1e-5)
            confidence = min(0.99, max(0.60, 0.50 + min(snr / 20.0, 0.49)))
            event_type = AudioEventType.SPEECH_PRESENT
        else:
            self.contiguous_speech_chunks = 0
            speech_dur = 0.0
            confidence = min(0.98, max(0.70, 1.0 - (rms / dynamic_threshold) * 0.3))
            event_type = AudioEventType.SILENCE

        return VADResult(
            is_speech=is_speech,
            event_type=event_type,
            confidence=round(confidence, 2),
            speech_duration=round(speech_dur, 2),
            energy_rms=round(rms, 2),
            zcr=round(zcr, 4),
            timestamp=now_iso,
        )
