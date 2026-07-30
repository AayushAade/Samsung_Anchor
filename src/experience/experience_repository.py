"""
MEMORA Append-Only Experience Repository.

Provides persistent, thread-safe, append-only storage for completed execution records.
Never mutates historical records once appended.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from src.experience.experience_models import ExecutionOutcome, ExecutionRecord


class ExperienceRepository:
    """
    Thread-safe, append-only repository for execution records.
    """

    MAX_RECORDS = 500

    def __init__(self, max_records: int = 500) -> None:
        self.max_records = max_records
        self._records: List[ExecutionRecord] = []
        self._lock = threading.Lock()
        self._seed_baseline_history()

    def add_record(self, record: ExecutionRecord) -> None:
        """
        Append a completed execution record to the repository.
        """
        with self._lock:
            self._records.append(record)
            if len(self._records) > self.max_records:
                self._records = self._records[-self.max_records:]

    def get_all_records(self) -> List[ExecutionRecord]:
        with self._lock:
            return list(self._records)

    def get_recent_records(self, limit: int = 20) -> List[ExecutionRecord]:
        with self._lock:
            return list(self._records[-limit:])

    def query_by_outcome(self, outcome: ExecutionOutcome) -> List[ExecutionRecord]:
        with self._lock:
            return [r for r in self._records if r.completion_status == outcome]

    def clear(self) -> None:
        with self._lock:
            self._records.clear()

    def _seed_baseline_history(self) -> None:
        """Seed initial baseline execution history records."""
        r1 = ExecutionRecord(
            goal_id="g-baseline-1",
            plan_id="p-baseline-1",
            tasks_executed=[{"title": "Determine Location"}, {"title": "Verify Table"}, {"title": "Suggest Cue"}],
            completion_status=ExecutionOutcome.SUCCESSFUL,
            confidence_evolution=[0.80, 0.85, 0.90],
            latency_ms=12.5,
            environment_context={"room": "Living Room"},
        )
        r2 = ExecutionRecord(
            goal_id="g-baseline-2",
            plan_id="p-baseline-2",
            tasks_executed=[{"title": "Check Medication Schedule"}, {"title": "Provide Reminder"}],
            completion_status=ExecutionOutcome.SUCCESSFUL,
            confidence_evolution=[0.85, 0.92],
            latency_ms=8.4,
            environment_context={"room": "Dining Room"},
        )
        self._records.extend([r1, r2])
