"""
MEMORA Performance Benchmark Suite.

Executes latency and throughput benchmarks across core database, vision, FAISS,
and memory repository operations.
"""

from __future__ import annotations

import time
from typing import Any, Callable
import numpy as np

from src.memory.database import MemoraDatabase
from src.vision.face_recognizer import MemoraFaceRecognizer


class BenchmarkSuite:
    """
    Performance benchmark harness for MEMORA subsystem operations.
    """

    def __init__(self, db: MemoraDatabase | None = None) -> None:
        self.db = db or MemoraDatabase("sqlite:///:memory:")
        self.recognizer = MemoraFaceRecognizer(mock_mode=True)

    def _benchmark_operation(
        self, name: str, func: Callable[[], Any], iterations: int = 50
    ) -> dict[str, Any]:
        """
        Execute an operation multiple times and collect timing statistics.
        """
        latencies_ms: list[float] = []

        # Warm-up run
        try:
            func()
        except Exception:
            pass

        start_total = time.perf_counter()
        for _ in range(iterations):
            t0 = time.perf_counter()
            func()
            t1 = time.perf_counter()
            latencies_ms.append((t1 - t0) * 1000.0)
        end_total = time.perf_counter()

        total_time_sec = max(end_total - start_total, 1e-6)
        sorted_latencies = sorted(latencies_ms)
        p95_index = int(0.95 * len(sorted_latencies))

        return {
            "operation": name,
            "iterations": iterations,
            "avg_ms": float(np.mean(sorted_latencies)),
            "min_ms": float(np.min(sorted_latencies)),
            "max_ms": float(np.max(sorted_latencies)),
            "p95_ms": float(sorted_latencies[min(p95_index, len(sorted_latencies) - 1)]),
            "throughput_ops_sec": float(iterations / total_time_sec),
        }

    def run_all_benchmarks(self, iterations: int = 50) -> dict[str, dict[str, Any]]:
        """
        Run complete suite of performance benchmarks.
        """
        results: dict[str, dict[str, Any]] = {}

        # 1. Identity lookup latency
        test_anon_id = self.db.register_anonymous(np.zeros(128, dtype=np.float32))
        results["identity_lookup"] = self._benchmark_operation(
            "Identity Lookup Latency",
            lambda: self.db.get_identity(test_anon_id),
            iterations=iterations,
        )

        # 2. FAISS Vector Search
        dummy_query = np.random.randn(128).astype(np.float32)
        results["vector_search"] = self._benchmark_operation(
            "FAISS Vector Search Latency",
            lambda: self.db.vector_store.find_match(dummy_query, 0.6),
            iterations=iterations,
        )

        # 3. Face Recognition Frame Processing
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        results["face_recognition"] = self._benchmark_operation(
            "Face Recognition Frame Latency",
            lambda: self.recognizer.process_frame(dummy_frame, self.db),
            iterations=iterations,
        )

        # 4. Object Logging Latency
        results["object_logging"] = self._benchmark_operation(
            "Object Location Logging Latency",
            lambda: self.db.log_object("reading_glasses", 10.0, 20.0, "Living Room"),
            iterations=iterations,
        )

        # 5. Database Commit Latency
        results["db_commit"] = self._benchmark_operation(
            "Database State Commit Latency",
            lambda: self.db.set_current_room("Living Room"),
            iterations=iterations,
        )

        # 6. Memory Retrieval Latency
        from src.cognition.memory_query import MemoryQuery
        results["memory_retrieval"] = self._benchmark_operation(
            "Memory Retrieval Latency",
            lambda: self.db.memory_repo.find(MemoryQuery(face_id="Eleanor")),
            iterations=iterations,
        )

        # 7. Episode Creation Latency
        from src.cognition.episode import Episode
        test_ep = Episode(person="Eleanor", summary="Test interaction episode summary")
        results["episode_creation"] = self._benchmark_operation(
            "Episode Creation Latency",
            lambda: self.db.episode_repo.add_episode(test_ep),
            iterations=iterations,
        )

        return results
