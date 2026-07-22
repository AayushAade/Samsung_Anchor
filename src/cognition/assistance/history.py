from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from src.cognition.assistance.models import AssistanceLevel


@dataclass
class SupportEvent:
    """
    Logs system intervention history.
    ETHICAL CONSTRAINT: Tracks support events, NOT patient diagnostic grades.
    """

    timestamp: datetime
    person_id: str
    level: AssistanceLevel
    trigger_reason: str
    outcome: str = "PENDING"


class ConfidenceHistory:
    """
    Maintains support history to inform deterministic escalation logic.
    """

    def __init__(self) -> None:
        self._history: List[SupportEvent] = []

    def log_event(
        self,
        person_id: str,
        level: AssistanceLevel,
        trigger_reason: str,
        outcome: str = "PENDING",
    ) -> SupportEvent:
        event = SupportEvent(
            timestamp=datetime.now(),
            person_id=person_id,
            level=level,
            trigger_reason=trigger_reason,
            outcome=outcome,
        )
        self._history.append(event)
        return event

    def get_recent_events(
        self, person_id: Optional[str] = None, limit: int = 5
    ) -> List[SupportEvent]:
        if person_id:
            filtered = [e for e in self._history if e.person_id == person_id]
            return filtered[-limit:]
        return self._history[-limit:]

    def get_last_event_for_person(
        self, person_id: str
    ) -> Optional[SupportEvent]:
        for e in reversed(self._history):
            if e.person_id == person_id:
                return e
        return None

    def clear() -> None:
        self._history.clear()
