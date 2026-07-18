"""
Context Restorer

Transforms memory records into minimal cognitive cues.
"""

from __future__ import annotations

from src.cognition.context_cue import (
    ContextCue,
    CueType,
)


class ContextRestorer:
    """
    Generates cognitive cues from memory.
    """

    def restore_identity(
        self,
        identity: dict | None,
    ) -> ContextCue:
        """
        Generate a cue for a recognized identity.
        """

        if not identity:
            return ContextCue(
                cue_type=CueType.IDENTITY,
                text="Unknown person.",
                priority=5,
                confidence=1.0,
            )

        name = identity.get("display_name")
        relationship = identity.get("relationship")

        if not name:
            return ContextCue(
                cue_type=CueType.IDENTITY,
                text="Unknown person.",
                priority=5,
            )

        if relationship:
            cue = f"{name}. {relationship}."
        else:
            cue = f"{name}."

        return ContextCue(
            cue_type=CueType.IDENTITY,
            text=cue,
            priority=10,
            confidence=identity.get("confidence", 1.0),
        )