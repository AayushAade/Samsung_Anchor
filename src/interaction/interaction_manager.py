"""
Interaction Manager.

Converts cognitive events into user-facing interaction actions.
"""

from __future__ import annotations

from src.cognition.reasoning_models import MemoryRecall
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
        recall: MemoryRecall | None = None,
    ) -> InteractionAction | None:
        """
        Convert a cognitive event into a user-facing action.
        """

        if event.type != PresenceEventType.PERSON_ARRIVED:
            return None

        message = f"{event.name} is here"

        if event.relationship:
            message += f". They are your {event.relationship}"

        message += "."

        # --------------------------------------------------
        # Memory-aware interaction
        # --------------------------------------------------

        if (
            recall is not None
            and recall.recalled_memories
        ):
            memory = recall.recalled_memories[0]

            if memory.summary:
                message += f" Last time you {memory.summary}"

            if memory.commitments:
                message += (
                    f" You also planned to "
                    f"{memory.commitments[0]}."
                )

        return InteractionAction(
            type=InteractionActionType.SPEAK,
            message=message,
        )