"""
Presence Engine.

Converts face recognition results into Presence Events.
"""

from __future__ import annotations

from typing import Any

from src.interaction.events import (
    PresenceEvent,
    PresenceEventType,
)


class PresenceEngine:
    """
    Tracks who has already appeared during a session.
    """

    def __init__(self) -> None:
        self._visible: set[str] = set()

    def process(
        self,
        result: dict[str, Any],
    ) -> PresenceEvent | None:
        """
        Process one recognition result and emit a PresenceEvent.
        """

        face_id = result.get("face_id")
        name = result.get("name")
        relationship = result.get("relationship")

        if not face_id:
            return None

        if face_id in self._visible:
            return None

        self._visible.add(face_id)

        if name is None:
            return PresenceEvent(
                type=PresenceEventType.UNKNOWN_PERSON_DETECTED,
                face_id=face_id,
                name=None,
            )

        return PresenceEvent(
            type=PresenceEventType.PERSON_ARRIVED,
            face_id=face_id,
            name=name,
            relationship=relationship,
        )

    def reset(self) -> None:
        """
        Reset session state.
        """

        self._visible.clear()
        