from datetime import datetime

from src.cognition.experience import Experience
from src.cognition.memory_encoder import MemoryEncoder
from src.cognition.memory_models import MemoryType


def test_encode_experience():

    encoder = MemoryEncoder()

    experience = Experience(
        timestamp=datetime.now(),
        people=["Alice"],
        location="Innovation Lab",
        transcript="Discussed Samsung prototype.",
        activity="Discussion",
    )

    memory = encoder.encode(experience)

    assert memory.memory_type == MemoryType.EPISODIC
    assert memory.person == "Alice"
    assert memory.location == "Innovation Lab"
    assert memory.title == "Discussion"
    assert memory.summary == "Discussed Samsung prototype."