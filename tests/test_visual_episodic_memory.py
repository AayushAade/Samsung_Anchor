import pytest
from src.perception.visual_memory_engine import VisualEpisodicMemoryEngine, VisualMemoryEntry
from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline


def test_visual_memory_entry_attributes():
    engine = VisualEpisodicMemoryEngine()
    entry = engine.record_observation(
        object_category="reading glasses",
        spatial_description="on the coffee table beside your newspaper",
        confidence=0.92,
        room="Living Room",
        patient_name="Eleanor",
    )

    assert entry.object_category == "reading glasses"
    assert entry.confidence == 0.92
    assert "coffee table" in entry.spatial_description
    assert entry.room == "Living Room"
    assert entry.associated_patient == "Eleanor"
    assert entry.observation_source == "Camera HAL (OpenCV)"


def test_visual_memory_recall_confidence_thresholds():
    engine = VisualEpisodicMemoryEngine()

    # 1. High Confidence (Reading Glasses)
    res_high = engine.recall_object_location("Where are my reading glasses?", "Eleanor")
    assert res_high["found"] is True
    assert "I last saw your reading glasses on the coffee table" in res_high["response"]

    # 2. Medium Confidence Uncertainty Statement (Television Remote)
    res_mid = engine.recall_object_location("Where is the television remote?", "Eleanor")
    assert res_mid["found"] is True
    assert "I think your television remote may still be on the dining table, but I'm not certain." in res_mid["response"]

    # 3. Low Confidence / Unknown Item
    res_unk = engine.recall_object_location("Where is my wallet?", "Eleanor")
    assert res_unk["found"] is False
    assert "I haven't seen that item recently" in res_unk["response"]


def test_visual_memory_scenarios_for_five_meaningful_items():
    engine = VisualEpisodicMemoryEngine()

    items = [
        ("reading glasses", "coffee table"),
        ("medication bottle", "kitchen counter"),
        ("walking cane", "armchair"),
        ("keys", "entryway table"),
        ("television remote", "dining table"),
    ]

    for item_name, location_keyword in items:
        res = engine.recall_object_location(f"Where is my {item_name}?", "Eleanor")
        assert res["found"] is True
        assert location_keyword in res["response"]


def test_cognitive_pipeline_integration_visual_episodic_memory():
    db = MemoraDatabase("sqlite:///:memory:")
    pipeline = CognitivePipeline(db)

    for m in pipeline.medication_mgr.get_missed_medications():
        pipeline.medication_mgr.mark_taken(m.med_id)

    rec_result = {
        "face_id": "1",
        "name": "Eleanor",
        "relationship": "Patient",
        "user_speech": "Where are my reading glasses?",
    }

    actions = pipeline.process(rec_result)

    assert len(actions) == 1
    action_msg = actions[0].message
    assert "coffee table" in action_msg.lower()

    # Verify decision trace recorded visual memory recall
    assert hasattr(pipeline, "latest_clinical_trace")
    trace = pipeline.latest_clinical_trace
    assert trace is not None
    assert trace.speech_produced is True

    pipeline.shutdown()
