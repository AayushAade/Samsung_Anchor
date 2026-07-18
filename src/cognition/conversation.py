from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Conversation:
    """
    Represents one completed interaction with a person.
    """

    person: str

    transcript: str

    timestamp: datetime = field(
        default_factory=datetime.now
    )

    location: str = ""

    summary: str = ""

    commitments: list[str] = field(default_factory=list)

    tags: list[str] = field(default_factory=list)