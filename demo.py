"""
Samsung Anchor Demo

First executable cognitive demonstration.
"""

from datetime import datetime

from src.cognition.experience import Experience
from src.cognition.memory_encoder import MemoryEncoder
from src.pipeline.cognitive_pipeline import CognitivePipeline


def main():

    print("=" * 60)
    print("🧠 Samsung Anchor Demo")
    print("=" * 60)

    pipeline = CognitivePipeline()
    encoder = MemoryEncoder()

    # ---------------------------------------------
    # Create a memory
    # ---------------------------------------------

    experience = Experience(
        timestamp=datetime.now(),
        people=["Alice"],
        activity="Samsung Meeting",
        transcript="discussed Samsung Anchor.",
    )

    memory = encoder.encode(experience)

    pipeline.memory_repository.save(memory)

    print("\nMemory stored.\n")

    # ---------------------------------------------
    # Simulate recognition
    # ---------------------------------------------

    recognition = {
        "face_id": "1",
        "name": "Alice",
        "relationship": "Friend",
    }

    actions = pipeline.process(recognition)

    print("Recognition Result:")
    print(recognition)

    print("\nAnchor Response:\n")

    for action in actions:
        print(action.message)


if __name__ == "__main__":
    main()