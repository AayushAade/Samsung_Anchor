"""
Samsung Anchor Live Demo

Live end-to-end demo using the Runtime and Coordinator.
Press 'q' to quit.
"""

from __future__ import annotations

import cv2

from devices.camera import CameraDevice
from devices.speaker import SpeakerDevice

from src.audio.audio_listener import MemoraAudioListener
from src.coordinator.anchor_coordinator import AnchorCoordinator
from src.memory.database import MemoraDatabase
from src.reasoning.context_binder import MemoraContextBinder
from src.runtime.runtime import AnchorRuntime
from src.vision.face_recognizer import MemoraFaceRecognizer


def main() -> None:

    print("=" * 60)
    print("🧠 Samsung Anchor Live Demo")
    print("=" * 60)

    camera = CameraDevice()

    if not camera.open():
        print("❌ Failed to open camera.")
        return

    database = MemoraDatabase()

    recognizer = MemoraFaceRecognizer(
        mock_mode=True
    )

    listener = MemoraAudioListener(mock_mode=True)

    binder = MemoraContextBinder()

    speaker = SpeakerDevice()

    coordinator = AnchorCoordinator(
        database=database,
        recognizer=recognizer,
        listener=listener,
        binder=binder,
        speaker=speaker,
    )

    runtime = AnchorRuntime(coordinator)

    runtime.initialize()
    runtime.start()

    print("\nCamera started. Press 'q' to quit.\n")

    try:

        while True:

            frame, results = runtime.run_once(camera)

            recognizer.draw_faces(
                frame,
                results,
            )

            actions = coordinator.consume_actions()

            for action in actions:
                speaker.execute(action)

            cv2.imshow(
                "Samsung Anchor Live Demo",
                frame,
            )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:

        runtime.shutdown()
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()