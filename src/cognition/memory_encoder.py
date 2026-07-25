from __future__ import annotations
from typing import Optional, Any
from src.cognition.experience import Experience
from src.cognition.memory_models import (
    RelevantMemory,
    MemoryType,
)


class MemoryEncoder:
    """
    Converts experiences into long-term memories.
    """

    def __init__(self, memory_repository: Optional[Any] = None) -> None:
        self.memory_repository = memory_repository

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

        mem = RelevantMemory(
            memory_id="temp",
            memory_type=MemoryType.EPISODIC,
            title=title,
            summary=summary,
            person=person,
            location=experience.location,
            timestamp=experience.timestamp,
        )

        if self.memory_repository is not None and summary and person:
            if hasattr(self.memory_repository, "save"):
                self.memory_repository.save(mem)
            elif hasattr(self.memory_repository, "save_memory"):
                self.memory_repository.save_memory(
                    person_name=person,
                    content=summary,
                    location=experience.location,
                    memory_type=MemoryType.EPISODIC,
                )

        return mem

    def encode_experience(
        self,
        person_name: str,
        location: str,
        content: str,
        context: str = "Interaction",
    ) -> RelevantMemory:
        from datetime import datetime
        exp = Experience(
            timestamp=datetime.now(),
            people=[person_name] if person_name else [],
            location=location or "Living Room",
            transcript=content or "",
            activity=context,
        )
        return self.encode(exp)