import time
from typing import Dict, Optional

class MetricsRegistry:
    """
    Centralized registry for tracking system performance and latency.
    """
    def __init__(self):
        self._latencies: Dict[str, list[float]] = {}
        self._counts: Dict[str, int] = {}
        self._active_timers: Dict[str, float] = {}

    def start_timer(self, metric_name: str):
        self._active_timers[metric_name] = time.perf_counter()

    def stop_timer(self, metric_name: str) -> float:
        if metric_name not in self._active_timers:
            return 0.0
            
        elapsed = time.perf_counter() - self._active_timers[metric_name]
        del self._active_timers[metric_name]
        
        if metric_name not in self._latencies:
            self._latencies[metric_name] = []
        self._latencies[metric_name].append(elapsed)
        
        return elapsed

    def increment(self, counter_name: str, amount: int = 1):
        if counter_name not in self._counts:
            self._counts[counter_name] = 0
        self._counts[counter_name] += amount

    def get_average_latency(self, metric_name: str) -> Optional[float]:
        l = self._latencies.get(metric_name)
        if not l: return None
        return sum(l) / len(l)
        
    def summary(self) -> str:
        s = "--- System Metrics Summary ---\n"
        for name in sorted(self._latencies.keys()):
            s += f"{name} (Avg): {self.get_average_latency(name):.4f}s\n"
        for name, count in sorted(self._counts.items()):
            s += f"{name} (Count): {count}\n"
        return s

# Global singleton for easy import across subsystems
metrics = MetricsRegistry()
