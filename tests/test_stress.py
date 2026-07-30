import time
from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline


def test_stress_continuous_execution():
    db = MemoraDatabase("sqlite:///:memory:")
    pipeline = CognitivePipeline(db)

    rec = {
        "faces": [{"face_id": "Face_Stress", "name": "Sarah", "confidence": 0.95}]
    }

    start_time = time.perf_counter()
    cycles = 50

    for i in range(cycles):
        actions = pipeline.process(rec)
        assert isinstance(actions, list)

    elapsed = time.perf_counter() - start_time
    avg_latency = (elapsed / cycles) * 1000

    # Ensure average cycle latency is well under 100ms
    assert avg_latency < 100.0
