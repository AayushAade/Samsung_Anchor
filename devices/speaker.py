"""
Samsung Anchor Speaker Device.

Hardware abstraction for speech output.

The current implementation prints messages to stdout.
A future implementation will replace the print statement
with a real text-to-speech engine.
"""

from __future__ import annotations

from src.interaction.actions import (
    InteractionAction,
    InteractionActionType,
)


class SpeakerDevice:
    """
    Executes interaction actions.
    """

    def execute(
        self,
        action: InteractionAction,
    ) -> None:
        """
        Execute an interaction action.

        Currently supports SPEAK actions only.
        """

        if action.type == InteractionActionType.SPEAK:
            print(action.message)