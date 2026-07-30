"""
MEMORA Pattern Library.

Identifies and indexes reusable execution patterns from accumulated execution records.
Maintains deterministic metrics: usage count, success rate, average latency, failure causes.
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Dict, List, Optional

from src.experience.experience_models import ExecutionOutcome, ExecutionPattern, ExecutionRecord


class PatternLibrary:
    """
    Index of reusable operational execution patterns derived from execution records.
    """

    def __init__(self) -> None:
        self._patterns: Dict[str, ExecutionPattern] = {}
        self._lock = threading.Lock()
        self._seed_baseline_patterns()

    def update_from_execution(self, record: ExecutionRecord, goal_title: str) -> ExecutionPattern:
        """
        Extract or update an execution pattern from a completed execution record.
        """
        task_titles = [t.get("title", "Task") for t in record.tasks_executed]
        key = f"{goal_title.lower()}:{'-'.join(task_titles)}"

        with self._lock:
            if key in self._patterns:
                pat = self._patterns[key]
                pat.usage_count += 1
                if record.completion_status in (ExecutionOutcome.SUCCESSFUL, ExecutionOutcome.RECOVERED):
                    pat.success_count += 1
                    pat.last_successful_iso = record.timestamp_iso
                pat.success_rate = round(pat.success_count / pat.usage_count, 3)
                pat.average_latency_ms = round(0.8 * pat.average_latency_ms + 0.2 * record.latency_ms, 2)
            else:
                is_success = record.completion_status in (ExecutionOutcome.SUCCESSFUL, ExecutionOutcome.RECOVERED)
                pat = ExecutionPattern(
                    goal_title=goal_title,
                    task_sequence_titles=task_titles,
                    usage_count=1,
                    success_count=1 if is_success else 0,
                    success_rate=1.0 if is_success else 0.0,
                    average_latency_ms=record.latency_ms,
                    average_confidence=0.85,
                )
                self._patterns[key] = pat
            return pat

    def find_recommended_pattern(self, goal_title_keyword: str) -> Optional[ExecutionPattern]:
        """
        Return the highest success rate pattern matching the goal keyword.
        """
        kw = goal_title_keyword.lower()
        with self._lock:
            matching = [p for p in self._patterns.values() if kw in p.goal_title.lower()]
            if not matching:
                return None
            matching.sort(key=lambda p: (p.success_rate, p.usage_count), reverse=True)
            return matching[0]

    def get_all_patterns(self) -> List[ExecutionPattern]:
        with self._lock:
            return list(self._patterns.values())

    def _seed_baseline_patterns(self) -> None:
        """Seed initial baseline execution patterns."""
        p1 = ExecutionPattern(
            goal_title="Locate Reading Glasses",
            task_sequence_titles=["Determine last known location", "Verify resting place in Living Room", "Suggest retrieval cue to user"],
            usage_count=8,
            success_count=7,
            success_rate=0.875,
            average_latency_ms=11.2,
            average_confidence=0.88,
        )
        p2 = ExecutionPattern(
            goal_title="Assist Medication Routine",
            task_sequence_titles=["Check medication schedule and pending dosage", "Provide gentle medication reminder prompt"],
            usage_count=12,
            success_count=12,
            success_rate=1.0,
            average_latency_ms=8.5,
            average_confidence=0.92,
        )
        self._patterns["locate glasses"] = p1
        self._patterns["medication"] = p2
