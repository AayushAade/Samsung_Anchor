"""
MEMORA Patient Timeline Generator.

Maintains a thread-safe, verifiable chronological timeline of patient events recorded across
cognitive assistance sessions. Never infers unobserved events.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from src.caregiver.caregiver_models import TimelineEvent, TimelineEventType


class PatientTimeline:
    """
    Thread-safe chronological patient event log and query provider.
    Enforces deterministic event ordering and timeline filtering capabilities.
    """

    def __init__(self) -> None:
        self._events: List[TimelineEvent] = []
        self._lock = threading.Lock()

    def add_event(
        self,
        event_type: TimelineEventType,
        description: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TimelineEvent:
        """
        Record a verified timeline event.
        """
        evt = TimelineEvent(
            event_type=event_type,
            description=description,
            session_id=session_id,
            metadata=metadata or {},
        )
        with self._lock:
            self._events.append(evt)
            return evt

    def get_all_events(self) -> List[TimelineEvent]:
        """Return all recorded timeline events in chronological order."""
        with self._lock:
            return list(self._events)

    def get_daily_timeline(self, date_prefix: Optional[str] = None) -> List[TimelineEvent]:
        """
        Return timeline events filtered by ISO date prefix (e.g. '2026-07-30').
        If date_prefix is None, returns all events recorded today.
        """
        with self._lock:
            if not date_prefix:
                return list(self._events)
            return [e for e in self._events if e.timestamp.startswith(date_prefix)]

    def get_weekly_timeline(self) -> List[TimelineEvent]:
        """
        Return all events recorded during the current observation window.
        """
        with self._lock:
            return list(self._events)

    def get_session_timeline(self, session_id: str) -> List[TimelineEvent]:
        """
        Return timeline events for a specific cognitive session ID.
        """
        with self._lock:
            return [e for e in self._events if e.session_id == session_id]

    def get_events_by_type(self, event_type: TimelineEventType) -> List[TimelineEvent]:
        """
        Return timeline events matching a specific TimelineEventType.
        """
        with self._lock:
            return [e for e in self._events if e.event_type == event_type]

    def get_event_count(self) -> int:
        """Return total number of recorded events."""
        with self._lock:
            return len(self._events)

    def get_latest_event(self) -> Optional[TimelineEvent]:
        """Return the most recently recorded event, or None if timeline is empty."""
        with self._lock:
            return self._events[-1] if self._events else None

    def clear(self) -> None:
        """Clear timeline events cache."""
        with self._lock:
            self._events.clear()
