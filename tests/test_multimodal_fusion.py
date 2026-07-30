from src.perception.multimodal_fusion import MultimodalFusionEngine
from src.perception.sensor_models import (
    ActivityType,
    AudioEvent,
    AudioEventType,
    RoomLocation,
)


def test_multimodal_fusion_conflict_resolution():
    engine = MultimodalFusionEngine()

    distress_audio = AudioEvent(event_type=AudioEventType.CRYING)
    ctx = engine.fuse(
        room=RoomLocation.LIVING_ROOM,
        activity=ActivityType.WALKING,
        faces=[],
        objects=[],
        audio_events=[distress_audio],
    )

    # Distress audio overrides walking activity to FALLEN
    assert ctx.detected_activity == ActivityType.FALLEN
