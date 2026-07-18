"""
Cue Formatter.

Converts ContextCue objects into presentation text.

The formatter knows HOW a cue should be presented,
while ContextRestorer knows WHAT information should
be conveyed.
"""

from __future__ import annotations

from src.cognition.context_cue import ContextCue


class CueFormatter:
    """
    Converts cognitive cues into user-facing text.
    """

    def format(
        self,
        cue: ContextCue,
    ) -> str:
        """
        Convert a cue into a display/speech string.
        """

        return cue.text.strip()