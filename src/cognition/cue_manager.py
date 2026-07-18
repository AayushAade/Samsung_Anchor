"""
Cue Manager

Manages cognitive cues before they are delivered to the user.

Responsibilities
----------------
- Accept new cues.
- Prioritize cues.
- Deliver the highest-priority cue.
- Clear pending cues.
"""

from __future__ import annotations

from src.cognition.context_cue import ContextCue


class CueManager:
    """
    Manages pending cognitive cues.
    """

    def __init__(self) -> None:
        self._queue: list[ContextCue] = []

    def add(
        self,
        cue: ContextCue,
    ) -> None:
        """
        Add a cue to the queue.
        """

        self._queue.append(cue)

        self._queue.sort(
            key=lambda c: c.priority,
            reverse=True,
        )

    def next(
        self,
    ) -> ContextCue | None:
        """
        Return the highest-priority cue.

        Returns None if the queue is empty.
        """

        if not self._queue:
            return None

        return self._queue.pop(0)

    def clear(self) -> None:
        """
        Remove all pending cues.
        """

        self._queue.clear()

    def __len__(self) -> int:
        """
        Number of pending cues.
        """

        return len(self._queue)