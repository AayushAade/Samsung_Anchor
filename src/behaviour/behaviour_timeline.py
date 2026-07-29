"""
MEMORA Behaviour Timeline.

Longitudinal activity timeline recording observable daily activity patterns,
routine stability scores, recurring object movements, and social interactions.
All entries link back to underlying evidence records.
"""

from __future__ import annotations

import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.behaviour.models import BehaviourTimelineEntry


class BehaviourTimeline:
    """
    Longitudinal behaviour timeline generator and repository.
    """

    MAX_ENTRIES = 500

    def __init__(self, max_entries: int = 500) -> None:
        self.max_entries = max_entries
        self._entries: List[BehaviourTimelineEntry] = []
        self._lock = threading.Lock()

    def record_activity(
        self,
        activity_name: str,
        location: str,
        duration_mins: float = 15.0,
        stability_score: float = 0.85,
        evidence_ids: Optional[List[str]] = None,
    ) -> BehaviourTimelineEntry:
        """
        Record a longitudinal activity event in the timeline.
        """
        entry_id = f"btl-{uuid.uuid4().hex[:8]}"
        entry = BehaviourTimelineEntry(
            entry_id=entry_id,
            timestamp_iso=datetime.now().isoformat(),
            activity_name=activity_name,
            location=location,
            duration_mins=duration_mins,
            stability_score=stability_score,
            supporting_evidence_ids=evidence_ids or [],
        )

        with self._lock:
            self._entries.append(entry)
            if len(self._entries) > self.max_entries:
                self._entries = self._entries[-self.max_entries:]

        return entry

    def get_recent_entries(self, limit: int = 20) -> List[BehaviourTimelineEntry]:
        with self._lock:
            return list(self._entries[-limit:])

    def generate_markdown(self) -> str:
        """Generate formatted Markdown timeline of longitudinal behaviour."""
        with self._lock:
            entries = list(self._entries[-15:])

        if not entries:
            return "No longitudinal behaviour timeline entries recorded."

        lines = [
            "### MEMORA Longitudinal Behaviour Timeline",
            "",
            "| Time | Activity | Location | Duration | Stability | Evidence Count |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for e in entries:
            t_str = e.timestamp_iso[11:16]
            lines.append(
                f"| {t_str} | **{e.activity_name}** | {e.location} | {e.duration_mins:.0f}m | {e.stability_score:.0%} | {len(e.supporting_evidence_ids)} |"
            )

        return "\n".join(lines)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
