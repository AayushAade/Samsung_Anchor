"""
Samsung Anchor Live Demo

Live camera + face recognizer + cognitive pipeline.
Press 'q' to quit.
"""

from devices.camera import CameraDevice
from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline
from src.vision.face_recognizer import MemoraFaceRecognizer

import cv2


def main():

    print("=" * 60)
    print("🧠 Samsung Anchor Live Demo")
    print("=" * 60)

    camera = CameraDevice()

    if not camera.open():
        print("❌ Failed to open camera.")
        return

    database = MemoraDatabase()

    # Start with mock mode so the pipeline is verified first.
    recognizer = MemoraFaceRecognizer(mock_mode=True)

    pipeline = CognitivePipeline()

    print("\nCamera started. Press 'q' to quit.\n")

    try:

        while True:

            success, frame = camera.read()

            if not success:
                print("Failed to capture frame.")
                break

            results = recognizer.process_frame(
                frame,
                database,
            )

            for result in results:

                actions = pipeline.process(result)

                for action in actions:
                    print(f"\n🧠 {action.message}")

            recognizer.draw_faces(frame, results)

            cv2.imshow(
                "Samsung Anchor Live Demo",
                frame,
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    finally:

        camera.release()

        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()