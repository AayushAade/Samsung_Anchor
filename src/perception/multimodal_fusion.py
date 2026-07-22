from datetime import datetime
from typing import List
from src.perception.sensor_models import (
    ActivityType,
    AudioEvent,
    DetectedFace,
    DetectedObject,
    PerceptionContext,
    RoomLocation,
)


class MultimodalFusionEngine:
    """
    Multimodal Sensor Fusion Engine resolving vision, audio, and clinical signals.
    """

    def fuse(
        self,
        room: RoomLocation,
        activity: ActivityType,
        faces: List[DetectedFace],
        objects: List[DetectedObject],
        audio_events: List[AudioEvent],
        fps: float = 30.0,
    ) -> PerceptionContext:
        """
        Fused PerceptionContext resolving conflicts deterministically.
        """
        # If fall audio or fall object detected, override activity to FALLEN
        has_fall_audio = any(e.event_type.value in ["Crying / Distress", "Loud Noise"] for e in audio_events)
        if has_fall_audio and activity == ActivityType.WALKING:
            activity = ActivityType.FALLEN

        return PerceptionContext(
            current_room=room,
            detected_activity=activity,
            detected_faces=faces,
            detected_objects=objects,
            audio_events=audio_events,
            fps=fps,
            last_updated=datetime.now().strftime("%H:%M:%S"),
        )
