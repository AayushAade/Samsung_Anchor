import time
from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline


def test_performance_latency_bounds():
    db = MemoraDatabase("sqlite:///:memory:")
    pipeline = CognitivePipeline(db)

    rec = {
        "faces": [{"face_id": "Face_Perf", "name": "Sarah", "confidence": 0.95}]
    }

    start = time.perf_counter()
    pipeline.process(rec)
    latency_ms = (time.perf_counter() - start) * 1000

    # Pipeline latency should be under 50ms in memory mode
    assert latency_ms < 50.0
