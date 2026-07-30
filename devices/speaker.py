"""
Samsung Anchor Speaker Device.

Hardware abstraction for speech output.

Uses the native macOS speech engine.
"""

from __future__ import annotations

import subprocess

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
        """

        if action.type != InteractionActionType.SPEAK:
            return

        # Still print for debugging/logging
        print(action.message)

        try:
            subprocess.Popen(
                [
                    "say",
                    action.message,
                ]
            )
        except Exception as e:
            print(f"[Speaker Error] {e}")