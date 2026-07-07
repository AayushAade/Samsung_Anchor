"""
Samsung Anchor Presence Engine.

Tracks visible identities during a session and determines
whether greeting actions should be triggered.
"""

from __future__ import annotations

from typing import Any


class PresenceEngine:
    """
    Handles presence-related behaviour.

    Responsibilities
    ----------------
    - Track greeted identities.
    - Generate greeting messages.
    """

    def __init__(self) -> None:
        self._greeted: set[str] = set()

    def process(self, result: dict[str, Any]) -> str | None:
        """
        Process one face recognition result.

        Returns
        -------
        str | None
            Greeting text if a greeting should be spoken,
            otherwise None.
        """

        face_id = result.get("face_id")
        name = result.get("name")
        relationship = result.get("relationship")

        if not face_id or not name:
            return None

        if face_id in self._greeted:
            return None

        self._greeted.add(face_id)

        greeting = f"{name} is here"

        if relationship:
            greeting += f". They are your {relationship}"

        greeting += "."

        return greeting

    def reset(self) -> None:
        """
        Reset session state.
        """

        self._greeted.clear()