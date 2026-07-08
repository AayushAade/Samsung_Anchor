from __future__ import annotations

from src.cognition.experience import Experience
from src.cognition.memory_models import (
    RelevantMemory,
    MemoryType,
)


class MemoryEncoder:
    """
    Converts experiences into long-term memories.
    """

    def encode(
        self,
        experience: Experience,
    ) -> RelevantMemory:

        title = experience.activity or "Interaction"

        summary = experience.transcript.strip()

        person = (
            experience.people[0]
            if experience.people
            else None
        )

        return RelevantMemory(
            memory_id="temp",
            memory_type=MemoryType.EPISODIC,
            title=title,
            summary=summary,
            person=person,
            location=experience.location,
            timestamp=experience.timestamp,
        )