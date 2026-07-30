"""
MEMORA Runtime Telemetry & Resource Monitoring Collector.

Tracks system resource metrics (CPU, RAM, threads, handles) and runtime telemetry
(recognition counts, database writes, recovery events, exceptions).
"""

from __future__ import annotations

import os
import sys
import time
import threading
from typing import Any

try:
    import psutil
except ImportError:
    psutil = None


class TelemetryCollector:
    """
    Lightweight telemetry and resource usage collector.
    """

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.start_time = time.time()
        self.shutdown_time: float | None = None

        # Resource monitoring samples
        self.cpu_samples: list[float] = []
        self.ram_samples_mb: list[float] = []
        self.thread_counts: list[int] = []

        # Telemetry counters
        self.counters: dict[str, int] = {
            "recognition_count": 0,
            "retrieval_count": 0,
            "db_writes": 0,
            "camera_reconnects": 0,
            "microphone_reconnects": 0,
            "runtime_exceptions": 0,
            "warning_count": 0,
            "processed_frames": 0,
        }

        self._process = psutil.Process(os.getpid()) if psutil else None

    def record_metric(self, name: str, increment: int = 1) -> None:
        """Increment a telemetry counter."""
        with self.lock:
            if name in self.counters:
                self.counters[name] += increment
            else:
                self.counters[name] = increment

    def sample_resources(self) -> dict[str, float]:
        """
        Take a snapshot of current system resource consumption.
        """
        cpu = 0.0
        ram_mb = 0.0
        num_threads = threading.active_count()

        if self._process:
            try:
                cpu = self._process.cpu_percent(interval=None)
                ram_mb = self._process.memory_info().rss / (1024 * 1024)
            except Exception:
                pass

        with self.lock:
            self.cpu_samples.append(cpu)
            self.ram_samples_mb.append(ram_mb)
            self.thread_counts.append(num_threads)

        return {
            "cpu_percent": cpu,
            "ram_mb": ram_mb,
            "num_threads": num_threads,
        }

    def mark_shutdown(self) -> None:
        """Record runtime shutdown timestamp."""
        with self.lock:
            self.shutdown_time = time.time()

    def get_summary(self) -> dict[str, Any]:
        """
        Get aggregated telemetry and resource summary metrics.
        """
        with self.lock:
            uptime = (self.shutdown_time or time.time()) - self.start_time
            avg_cpu = float(sum(self.cpu_samples) / len(self.cpu_samples)) if self.cpu_samples else 0.0
            peak_cpu = float(max(self.cpu_samples)) if self.cpu_samples else 0.0
            avg_ram = float(sum(self.ram_samples_mb) / len(self.ram_samples_mb)) if self.ram_samples_mb else 0.0
            peak_ram = float(max(self.ram_samples_mb)) if self.ram_samples_mb else 0.0
            peak_threads = max(self.thread_counts) if self.thread_counts else threading.active_count()
            frame_rate = float(self.counters.get("processed_frames", 0) / max(uptime, 1e-3))

            return {
                "uptime_seconds": uptime,
                "startup_timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_time)),
                "shutdown_timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.shutdown_time)) if self.shutdown_time else "RUNNING",
                "avg_cpu_percent": avg_cpu,
                "peak_cpu_percent": peak_cpu,
                "avg_ram_mb": avg_ram,
                "peak_ram_mb": peak_ram,
                "peak_threads": peak_threads,
                "frame_rate_fps": frame_rate,
                "counters": dict(self.counters),
            }
