"""
MEMORA Cognitive Drift Monitor.

Tracks longitudinal observable behavioral metrics over time windows (7-30 days)
and detects statistically meaningful trend shifts.

Strict Guardrail:
- Reports ONLY observable metric changes ("Object search frequency increased by 15%")
- NEVER infers medical conditions or diagnoses
- ALWAYS includes evidence summaries
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from src.behaviour.models import DriftMetric


class CognitiveDriftMonitor:
    """
    Non-medical longitudinal trend monitor tracking observable cognitive/behavioral signals.
    """

    def __init__(self, window_days: int = 30) -> None:
        self.window_days = window_days
        # Metric Name -> List of (timestamp, value)
        self._metric_history: Dict[str, List[tuple[float, float]]] = {}
        self._lock = threading.Lock()

        # Initialize default observable metric baselines
        self._initialize_default_metrics()

    def record_metric(self, metric_name: str, value: float) -> None:
        """
        Record a numerical observation for a drift metric.
        """
        now = time.time()
        with self._lock:
            if metric_name not in self._metric_history:
                self._metric_history[metric_name] = []
            self._metric_history[metric_name].append((now, value))

            # Prune metrics older than window_days * 2
            max_age = self.window_days * 2 * 86400.0
            self._metric_history[metric_name] = [
                (t, v) for t, v in self._metric_history[metric_name] if (now - t) <= max_age
            ]

    def evaluate_trends(self) -> List[DriftMetric]:
        """
        Compute longitudinal trend metrics over the configured window.
        """
        metrics: List[DriftMetric] = []
        now = time.time()
        window_sec = self.window_days * 86400.0
        midpoint = now - window_sec

        with self._lock:
            for name, history in self._metric_history.items():
                if not history:
                    continue

                baseline_vals = [v for t, v in history if t < midpoint]
                current_vals = [v for t, v in history if t >= midpoint]

                base_avg = sum(baseline_vals) / len(baseline_vals) if baseline_vals else (current_vals[0] if current_vals else 1.0)
                curr_avg = sum(current_vals) / len(current_vals) if current_vals else base_avg

                if base_avg == 0:
                    pct_change = 0.0
                else:
                    pct_change = ((curr_avg - base_avg) / base_avg) * 100.0

                is_sig = abs(pct_change) >= 15.0 and len(current_vals) >= 3

                direction = "increased" if pct_change > 0 else "decreased"
                summary = (
                    f"Observable trend: '{name}' {direction} by {abs(pct_change):.1f}% "
                    f"over the last {self.window_days} days compared with baseline."
                )

                metrics.append(
                    DriftMetric(
                        metric_name=name,
                        baseline_value=base_avg,
                        current_value=curr_avg,
                        pct_change=pct_change,
                        window_days=self.window_days,
                        is_statistically_significant=is_sig,
                        evidence_summary=summary,
                    )
                )

        return metrics

    def _initialize_default_metrics(self) -> None:
        """Seed initial observable metrics for tracking."""
        now = time.time()
        # Seed baseline observations (15 days ago vs recent)
        fifteen_days = 15 * 86400.0
        defaults = {
            "object_search_frequency": [(now - fifteen_days, 1.0), (now - 100, 1.2)],
            "repeated_questions_count": [(now - fifteen_days, 0.5), (now - 100, 0.5)],
            "response_latency_ms": [(now - fifteen_days, 120.0), (now - 100, 125.0)],
            "recognition_confidence": [(now - fifteen_days, 0.90), (now - 100, 0.92)],
        }
        for k, v in defaults.items():
            self._metric_history[k] = list(v)
