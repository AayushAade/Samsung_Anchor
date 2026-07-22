from datetime import datetime
from typing import List, Optional
from src.perception.sensor_models import AudioEvent, AudioEventType


class AudioPipeline:
    """
    Audio event processing pipeline.
    Detects non-transcribed audio events (Speech, Silence, Calling Name, Crying, Alarms).
    """

    def __init__(self) -> None:
        self._history: List[AudioEvent] = []

    def detect_event(self, event_type: AudioEventType = AudioEventType.SILENCE, confidence: float = 0.95) -> AudioEvent:
        evt = AudioEvent(
            event_type=event_type,
            confidence=confidence,
            timestamp=datetime.now().strftime("%H:%M:%S"),
        )
        self._history.append(evt)
        if len(self._history) > 20:
            self._history.pop(0)
        return evt

    def get_recent_audio_events(self, limit: int = 5) -> List[AudioEvent]:
        return self._history[-limit:]
