from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Experience:
    """
    A single real-world interaction observed by Anchor.

    Experiences are transient.
    They may or may not become long-term memories.
    """

    timestamp: datetime

    people: list[str] = field(default_factory=list)

    location: str | None = None

    transcript: str = ""

    detected_objects: list[str] = field(default_factory=list)

    activity: str | None = None