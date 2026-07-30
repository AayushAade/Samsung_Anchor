from src.perception.audio_pipeline import AudioPipeline
from src.perception.sensor_models import AudioEventType


def test_audio_pipeline_events():
    pipeline = AudioPipeline()
    evt = pipeline.detect_event(AudioEventType.CALLING_NAME)

    assert evt.event_type == AudioEventType.CALLING_NAME
    assert len(pipeline.get_recent_audio_events()) == 1
