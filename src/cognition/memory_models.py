from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MemoryType(Enum):
    """
    Categories of long-term memory.
    """

    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROSPECTIVE = "prospective"


class MemoryImportance(Enum):
    """
    Relative importance of a memory.
    """

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True)
class RelevantMemory:
    """
    A memory judged relevant to the current situation.
    """

    memory_id: str

    memory_type: MemoryType

    importance: MemoryImportance = MemoryImportance.NORMAL

    title: str = ""

    summary: str = ""

    person: str | None = None

    location: str | None = None

    timestamp: datetime | None = None

    commitments: list[str] = field(default_factory=list)

    tags: list[str] = field(default_factory=list)
    
    historical_usefulness: float = 0.5
    
    confidence: float = 1.0