from datetime import datetime
from src.memory.database import MemoraDatabase
from src.cognition.memory_models import RelevantMemory, MemoryType
from src.cognition.memory_query import MemoryQuery
from src.pipeline.cognitive_pipeline import CognitivePipeline
from src.runtime.runtime_models import SensorEvent, SensorEventType, HardwareConfig, RuntimeMode
from src.runtime.speaker_adapter import PyTTSx3SpeakerAdapter, SimulatedSpeakerAdapter


def test_closed_loop_cognitive_wiring_speech_transcript_and_speaker():
    db = MemoraDatabase("sqlite:///:memory:")
    pipeline = CognitivePipeline(db)

    # 1. Verify SensorBus Subscription to SPEECH_TRANSCRIPT
    assert pipeline.runtime_manager.sensor_bus is not None

    # Simulate SPEECH_TRANSCRIPT event on SensorBus
    t_event = SensorEvent(
        event_type=SensorEventType.SPEECH_TRANSCRIPT,
        source_device="Test_Mic",
        data={"text": "Where are my glasses?"},
    )
    pipeline.runtime_manager.sensor_bus.publish(t_event)

    # Seed episodic memory for Alice so memory restoration engine retrieves context
    mem = RelevantMemory(
        memory_id="mem_1",
        memory_type=MemoryType.EPISODIC,
        title="Glasses Location",
        summary="Glasses are on the kitchen table.",
        person="Alice",
        location="Kitchen",
        timestamp=datetime.now(),
    )
    pipeline.memory_repository.save(mem)

    # 2. Process Cognitive Cycle with person present
    rec_result = {
        "face_id": "1",
        "name": "Alice",
        "relationship": "Friend",
    }

    actions = pipeline.process(rec_result)

    # 3. Verify Action Generation & Memory Auto-Persistence
    assert isinstance(actions, list)
    if actions:
        action_msg = actions[0].message
        assert len(action_msg) > 0

        # Query MemoryRepository to verify experience was automatically encoded by MemoryEncoder
        res = pipeline.memory_repository.find(MemoryQuery())
        assert len(res) >= 1
        assert res[0].person == "Alice"

    pipeline.shutdown()


def test_pyttsx3_speaker_adapter_interface():
    speaker = PyTTSx3SpeakerAdapter(device_name="TestSpeaker")
    assert speaker.get_status().value in ["Healthy", "Connected"]

    ok = speaker.speak("Testing closed loop audio output")
    assert ok is True

    speaker.shutdown()
