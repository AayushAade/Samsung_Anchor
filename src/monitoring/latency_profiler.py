"""
MEMORA Pipeline Latency Profiler (Phase 11 — Objective 4).

Instruments end-to-end pipeline stages to compute empirical latency metrics:
- Camera Frame Capture
- Face Detection & Bounding Box Extraction
- Face Recognition & Embedding Computation
- Object Detection & Spatial Mapping
- Speech Recognition / STT
- Memory Retrieval (FAISS + SQLite)
- Executive Cognitive Engine Reasoning
- Gemini LLM API Call
- Memory Persistence Write
- Self-Reflection Evaluation
- TTS Audio Generation

Calculates exact Average, Median, 95th Percentile (P95), and Maximum Latency (ms).
"""

from __future__ import annotations

import math
import threading
import time
from typing import Any, Dict, List, Optional


class ComponentTimer:
    """Context manager for timing individual pipeline components."""

    def __init__(self, profiler: "PipelineLatencyProfiler", component_name: str) -> None:
        self.profiler = profiler
        self.component_name = component_name
        self.start_time = 0.0

    def __enter__(self) -> "ComponentTimer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        elapsed_ms = (time.perf_counter() - self.start_time) * 1000.0
        self.profiler.record_latency(self.component_name, elapsed_ms)


class PipelineLatencyProfiler:
    """
    Thread-safe latency profiler tracking stage-by-stage runtime performance.
    """

    _instance: Optional["PipelineLatencyProfiler"] = None
    _lock = threading.RLock()

    def __init__(self) -> None:
        self._latencies: Dict[str, List[float]] = {}
        self._lock = threading.RLock()

    @classmethod
    def get_instance(cls) -> "PipelineLatencyProfiler":
        with cls._lock:
            if cls._instance is None:
                cls._instance = PipelineLatencyProfiler()
            return cls._instance

    def time_component(self, component_name: str) -> ComponentTimer:
        return ComponentTimer(self, component_name)

    def record_latency(self, component_name: str, latency_ms: float) -> None:
        with self._lock:
            if component_name not in self._latencies:
                self._latencies[component_name] = []
            self._latencies[component_name].append(latency_ms)

    def get_component_stats(self, component_name: str) -> Dict[str, float]:
        with self._lock:
            samples = self._latencies.get(component_name, [])
            if not samples:
                return {"count": 0, "avg_ms": 0.0, "median_ms": 0.0, "p95_ms": 0.0, "max_ms": 0.0}

            sorted_samples = sorted(samples)
            n = len(sorted_samples)
            avg = sum(sorted_samples) / n
            median = sorted_samples[n // 2] if n % 2 != 0 else (sorted_samples[n // 2 - 1] + sorted_samples[n // 2]) / 2.0
            p95_idx = min(n - 1, math.ceil(0.95 * n) - 1)
            p95 = sorted_samples[p95_idx]
            max_val = sorted_samples[-1]

            return {
                "count": n,
                "avg_ms": round(avg, 2),
                "median_ms": round(median, 2),
                "p95_ms": round(p95, 2),
                "max_ms": round(max_val, 2),
            }

    def get_full_report(self) -> Dict[str, Any]:
        with self._lock:
            report = {}
            for comp in self._latencies:
                report[comp] = self.get_component_stats(comp)
            return report

    def print_summary(self) -> None:
        report = self.get_full_report()
        print("\n⏱️  MEMORA PIPELINE LATENCY PROFILER REPORT")
        print("=" * 75)
        print(f" {'Component Name':<30} | {'Count':<6} | {'Avg (ms)':<8} | {'Med (ms)':<8} | {'P95 (ms)':<8} | {'Max (ms)':<8}")
        print("-" * 75)
        for comp, stats in report.items():
            print(f" {comp:<30} | {stats['count']:<6} | {stats['avg_ms']:<8.2f} | {stats['median_ms']:<8.2f} | {stats['p95_ms']:<8.2f} | {stats['max_ms']:<8.2f}")
        print("=" * 75 + "\n")

    def clear(self) -> None:
        with self._lock:
            self._latencies.clear()
