from datetime import datetime
from typing import List, Optional, Any
from src.perception.sensor_models import AudioEvent, AudioEventType
from src.perception.voice_activity_detector import VoiceActivityDetector, VADResult
from src.perception.speech_recognition_engine import SpeechRecognitionEngine, TranscriptionResult


class AudioPipeline:
    """
    Audio event processing pipeline.
    Integrates HAL MicrophoneAdapter audio streams with VoiceActivityDetector,
    SpeechRecognitionEngine, and SensorBus.
    Detects non-transcribed audio events and transcribes speech segments offline.
    """

    def __init__(
        self,
        microphone_adapter: Optional[Any] = None,
        sensor_bus: Optional[Any] = None,
        vad_detector: Optional[VoiceActivityDetector] = None,
        speech_engine: Optional[SpeechRecognitionEngine] = None,
    ) -> None:
        self.microphone_adapter = microphone_adapter
        self.sensor_bus = sensor_bus
        self.vad_detector = vad_detector or VoiceActivityDetector()
        self.speech_engine = speech_engine or SpeechRecognitionEngine()
        self._history: List[AudioEvent] = []
        self._speech_buffer: bytes = b""

    def set_microphone_adapter(self, adapter: Any) -> None:
        self.microphone_adapter = adapter

    def set_sensor_bus(self, bus: Any) -> None:
        self.sensor_bus = bus

    def process_audio_chunk(self) -> Optional[dict]:
        """
        Reads raw audio chunk from microphone adapter, executes Voice Activity Detection (VAD),
        transcribes speech segments using SpeechRecognitionEngine, and publishes payloads to SensorBus.
        """
        if self.microphone_adapter is None:
            return None

        chunk_data = self.microphone_adapter.read_chunk()
        raw_audio = chunk_data.get("raw_audio")

        # Run Voice Activity Detection
        vad_result: VADResult = self.vad_detector.process_chunk(raw_audio)

        # Attach VAD metadata to chunk
        chunk_data["vad"] = {
            "is_speech": vad_result.is_speech,
            "event_type": vad_result.event_type.value,
            "confidence": vad_result.confidence,
            "speech_duration": vad_result.speech_duration,
            "energy_rms": vad_result.energy_rms,
            "zcr": vad_result.zcr,
        }

        # Segment Accumulation & Offline ASR Transcription
        if raw_audio:
            if vad_result.is_speech:
                self._speech_buffer += raw_audio
                # Cap speech segment buffer at 15 seconds (480,000 bytes) to prevent memory inflation
                if len(self._speech_buffer) >= 480000:
                    transcription: TranscriptionResult = self.speech_engine.transcribe_segment(self._speech_buffer)
                    self._speech_buffer = b""

                    if transcription.transcript:
                        chunk_data["transcript"] = {
                            "text": transcription.transcript,
                            "confidence": transcription.confidence,
                            "language": transcription.language,
                            "latency_ms": transcription.processing_latency_ms,
                            "start_timestamp": transcription.start_timestamp,
                            "end_timestamp": transcription.end_timestamp,
                        }

                        if self.sensor_bus is not None:
                            from src.runtime.runtime_models import SensorEvent, SensorEventType
                            t_event = SensorEvent(
                                event_type=SensorEventType.SPEECH_TRANSCRIPT,
                                source_device=getattr(self.microphone_adapter, "device_name", "MicrophoneAdapter"),
                                data=chunk_data["transcript"],
                            )
                            self.sensor_bus.publish(t_event)
            elif self._speech_buffer:
                # Transcribe accumulated speech segment upon transition to silence
                transcription: TranscriptionResult = self.speech_engine.transcribe_segment(self._speech_buffer)
                self._speech_buffer = b""

                if transcription.transcript:
                    chunk_data["transcript"] = {
                        "text": transcription.transcript,
                        "confidence": transcription.confidence,
                        "language": transcription.language,
                        "latency_ms": transcription.processing_latency_ms,
                        "start_timestamp": transcription.start_timestamp,
                        "end_timestamp": transcription.end_timestamp,
                    }

                    if self.sensor_bus is not None:
                        from src.runtime.runtime_models import SensorEvent, SensorEventType
                        t_event = SensorEvent(
                            event_type=SensorEventType.SPEECH_TRANSCRIPT,
                            source_device=getattr(self.microphone_adapter, "device_name", "MicrophoneAdapter"),
                            data=chunk_data["transcript"],
                        )
                        self.sensor_bus.publish(t_event)

        # Update AudioPipeline history with VAD detected event
        evt = AudioEvent(
            event_type=vad_result.event_type,
            confidence=vad_result.confidence,
            timestamp=datetime.now().strftime("%H:%M:%S"),
        )
        self._history.append(evt)
        if len(self._history) > 20:
            self._history.pop(0)

        # Publish AUDIO_EVENT to SensorBus
        if self.sensor_bus is not None:
            from src.runtime.runtime_models import SensorEvent, SensorEventType
            event = SensorEvent(
                event_type=SensorEventType.AUDIO_EVENT,
                source_device=getattr(self.microphone_adapter, "device_name", "MicrophoneAdapter"),
                data=chunk_data,
            )
            self.sensor_bus.publish(event)

        return chunk_data

    def transcribe_audio_buffer(self, raw_pcm_bytes: bytes) -> TranscriptionResult:
        """
        Directly transcribes a raw PCM audio buffer using SpeechRecognitionEngine and publishes to SensorBus.
        """
        res = self.speech_engine.transcribe_segment(raw_pcm_bytes)
        if self.sensor_bus is not None:
            from src.runtime.runtime_models import SensorEvent, SensorEventType
            t_data = {
                "text": res.transcript,
                "confidence": res.confidence,
                "language": res.language,
                "latency_ms": res.processing_latency_ms,
                "start_timestamp": res.start_timestamp,
                "end_timestamp": res.end_timestamp,
            }
            t_event = SensorEvent(
                event_type=SensorEventType.SPEECH_TRANSCRIPT,
                source_device=getattr(self.microphone_adapter, "device_name", "MicrophoneAdapter"),
                data=t_data,
            )
            self.sensor_bus.publish(t_event)
        return res

    def detect_event(
        self,
        event_type: Optional[AudioEventType] = None,
        confidence: float = 0.95,
    ) -> AudioEvent:
        self.process_audio_chunk()

        if event_type is not None:
            evt = AudioEvent(
                event_type=event_type,
                confidence=confidence,
                timestamp=datetime.now().strftime("%H:%M:%S"),
            )
            self._history.append(evt)
            if len(self._history) > 20:
                self._history.pop(0)
            return evt

        if self._history:
            return self._history[-1]

        return AudioEvent(
            event_type=AudioEventType.SILENCE,
            confidence=0.95,
            timestamp=datetime.now().strftime("%H:%M:%S"),
        )

    def get_recent_audio_events(self, limit: int = 5) -> List[AudioEvent]:
        return self._history[-limit:]
