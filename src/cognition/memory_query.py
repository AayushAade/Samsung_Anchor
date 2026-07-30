from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryQuery:
    """
    Describes the current situation for memory retrieval.
    """

    face_id: str | None = None

    location: str | None = None

    current_activity: str | None = None

    max_results: int = 3