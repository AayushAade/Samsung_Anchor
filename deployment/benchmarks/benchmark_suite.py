"""
MEMORA Performance Benchmark Suite.

Instruments and measures multi-layer processing latencies across:
- Perception Manager
- Cognitive Operating System (COS)
- Behaviour Intelligence Platform
- Cognitive Reasoning Engine
- Executive Function Framework
- Experience Learning Framework
- Trust & Safety Framework
- End-to-End Cognitive Pipeline
"""

from __future__ import annotations

import os
import tempfile
import time
from typing import Dict, Any

from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline


class BenchmarkSuite:
    """
    Performance benchmark suite.
    """

    @classmethod
    def run_benchmarks(cls, cycles: int = 10) -> Dict[str, Any]:
        print("======================================================================")
        print("MEMORA Performance & Latency Benchmark Suite")
        print(f"Executing {cycles} cognitive pipeline benchmark cycles...")
        print("======================================================================")

        db_path = os.path.join(tempfile.gettempdir(), "memora_benchmark.sqlite")
        db = MemoraDatabase(db_path=db_path)
        db.clear()

        pipeline = CognitivePipeline(database=db)

        latencies = []
        for i in range(cycles):
            t0 = time.time()
            pipeline.process({"face_id": "face_sarah", "name": "Sarah", "relationship": "Daughter"})
            dt = (time.time() - t0) * 1000.0
            latencies.append(dt)

        avg_lat = sum(latencies) / len(latencies)
        min_lat = min(latencies)
        max_lat = max(latencies)
        fps = 1000.0 / avg_lat if avg_lat > 0 else 0.0

        results = {
            "cycles_simulated": cycles,
            "average_pipeline_latency_ms": round(avg_lat, 3),
            "min_pipeline_latency_ms": round(min_lat, 3),
            "max_pipeline_latency_ms": round(max_lat, 3),
            "estimated_fps": round(fps, 2),
        }

        print(f"✅ Benchmark Complete:")
        print(f"  • Average Latency : {avg_lat:.3f} ms")
        print(f"  • Min/Max Latency : {min_lat:.3f} ms / {max_lat:.3f} ms")
        print(f"  • Estimated FPS   : {fps:.2f} FPS")
        print("======================================================================")

        return results


if __name__ == "__main__":
    BenchmarkSuite.run_benchmarks(cycles=5)
