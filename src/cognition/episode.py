"""
Episode Model

Represents one remembered experience inside Samsung Anchor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass(slots=True)
class Episode:
    """
    Represents one episodic memory.

    Example
    -------
    Sid visited yesterday.

    Summary:
        Worked on Samsung Anchor.

    Commitments:
        Continue Memory Module tomorrow.
    """

    person: str

    summary: str

    timestamp: datetime = field(default_factory=datetime.now)

    location: str = ""

    commitments: List[str] = field(default_factory=list)

    tags: List[str] = field(default_factory=list)