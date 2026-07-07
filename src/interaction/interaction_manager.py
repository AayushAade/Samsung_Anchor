"""
Interaction Manager.

Converts events into user-facing interaction actions.
"""

from __future__ import annotations

from src.interaction.actions import (
    InteractionAction,
    InteractionActionType,
)
from src.interaction.events import (
    PresenceEvent,
    PresenceEventType,
)


class InteractionManager:
    """
    Handles user-facing interaction decisions.
    """

    def handle_event(
        self,
        event: PresenceEvent,
    ) -> InteractionAction | None:

        if event.type == PresenceEventType.PERSON_ARRIVED:

            message = f"{event.name} is here"

            if event.relationship:
                message += f". They are your {event.relationship}"

            message += "."

            return InteractionAction(
                type=InteractionActionType.SPEAK,
                message=message,
            )

        return None