"""
Samsung Anchor Identity Learning Demo

Demonstrates the complete identity learning workflow without
requiring the live camera pipeline.
"""

from src.audio.audio_listener import MemoraAudioListener
from src.memory.database import MemoraDatabase
from src.reasoning.context_binder import MemoraContextBinder
from src.integration.identity_learning_pipeline import (
    process_identity_learning,
)


def main():

    print("=" * 60)
    print("🧠 Samsung Anchor Identity Learning Demo")
    print("=" * 60)

    database = MemoraDatabase()

    listener = MemoraAudioListener(
        mock_mode=True,
    )

    binder = MemoraContextBinder()

    import numpy as np
    dummy_embedding = np.zeros(128)
    face_id = database.register_anonymous(dummy_embedding)
    print(f"\nCreated identity: {face_id}")

    print("\nUnknown person detected.")
    print("Please introduce yourself.\n")

    transcript = listener.listen_and_transcribe()

    if not transcript:
        print("\nNo transcript received.")
        return

    result = process_identity_learning(
        face_id=face_id,
        transcript=transcript,
        database=database,
        binder=binder,
    )

    print("\nLearning Result:")
    print(result)

    identity = database.get_identity(face_id)

    print("\nStored Identity:")
    print(identity)


if __name__ == "__main__":
    main()