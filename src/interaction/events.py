"""
Samsung Anchor Events.

Shared event definitions used across the application.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PresenceEventType(Enum):
    """
    Presence-related events.
    """

    PERSON_ARRIVED = "person_arrived"
    PERSON_LEFT = "person_left"
    UNKNOWN_PERSON_DETECTED = "unknown_person_detected"


@dataclass(frozen=True)
class PresenceEvent:
    """
    Event emitted by the Presence Engine.
    """

    type: PresenceEventType
    face_id: str
    name: str | None
    relationship: str | None = None