"""
MEMORA Operational Runtime Metrics Aggregator.

Monitors and aggregates system resource metrics:
- CPU & memory usage
- Active thread counts
- Event queue depths
- Pipeline processing throughput (FPS)
"""

from __future__ import annotations

import os
import psutil
import threading
import time
from typing import Any, Dict


class RuntimeMetricsAggregator:
    """
    Operational resource metrics aggregator.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def capture_metrics(self) -> Dict[str, Any]:
        with self._lock:
            proc = psutil.Process(os.getpid())
            mem_info = proc.memory_info()
            mem_mb = mem_info.rss / (1024.0 * 1024.0)
            threads_count = proc.num_threads()

            return {
                "process_id": proc.pid,
                "memory_rss_mb": round(mem_mb, 2),
                "threads_count": threads_count,
                "cpu_percent": round(proc.cpu_percent(interval=None), 1),
                "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
