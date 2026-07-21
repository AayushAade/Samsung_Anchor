"""
Memora Experience Platform — Demo Launcher

Starts the complete Memora experience:
1. Initializes the Cognitive Engine (existing backend)
2. Starts the Experience Server (WebSocket + Dashboard)
3. Opens the dashboard in the default browser
4. Runs the camera loop with live cognitive processing

Usage:
    python demo_experience.py [--no-camera] [--scenario]

Flags:
    --no-camera   Run without a physical camera (uses scripted scenario)
    --scenario    Run the scripted Sarah medication demo scenario
"""

from __future__ import annotations

import sys
import time
import argparse
from datetime import datetime

from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline
from src.cognition.cognitive_memory_manager import CognitiveMemoryManager
from src.cognition.episode import Episode
from src.llm.reasoning_client import MockReasoningClient
from src.core.cognitive_stream import CognitiveStream
from experience.server import ExperienceServer


def run_scripted_scenario(pipeline: CognitivePipeline, db: MemoraDatabase):
    """
    Run the scripted Sarah medication demo scenario.
    Simulates multiple cognitive cycles with rich data.
    """
    
    print("\n🎬 Running Scripted Demo Scenario...\n")

    # Setup: Register Sarah
    face_id = "Face_1"
    db.bind_name(face_id, "Sarah", "Daughter")

    # Seed a memory via the consolidation path
    manager = CognitiveMemoryManager(db.SessionFactory, MockReasoningClient())
    ep = Episode(
        person=face_id,
        summary="Sarah reminded to take heart medication.",
        commitments=["Take heart pill"],
        timestamp=datetime.now(),
    )
    with db.SessionFactory() as session:
        from src.memory.models import EpisodeModel
        session.add(EpisodeModel(
            person=face_id,
            summary=ep.summary,
            timestamp=ep.timestamp.isoformat(),
            commitments=ep.commitments,
        ))
        session.commit()
    manager.process_episode(ep)
    manager.executor.shutdown(wait=True)

    recognition_result = {
        "face_id": face_id,
        "name": "Sarah",
        "relationship": "Daughter",
        "confidence": 0.99,
    }

    # ---- Cycle 1: First detection (no memories yet — Cognitive Silence) ----
    print("━" * 50)
    print("  Cycle 1: Sarah detected (first encounter)")
    print("━" * 50)
    pipeline.process(recognition_result)
    time.sleep(3)

    # ---- Cycle 2: Reset presence and detect again (with memories now) ----
    pipeline.reset()
    print("\n" + "━" * 50)
    print("  Cycle 2: Sarah detected again (with medical memory)")
    print("━" * 50)
    pipeline.process(recognition_result)
    time.sleep(3)

    # ---- Cycle 3: Unknown person ----
    pipeline.reset()
    print("\n" + "━" * 50)
    print("  Cycle 3: Unknown person detected")
    print("━" * 50)
    pipeline.process({
        "face_id": "Face_Unknown_1",
        "name": None,
        "relationship": None,
        "confidence": 0.85,
    })
    time.sleep(3)

    # ---- Cycle 4: Sarah returns (goal reinforcement) ----
    pipeline.reset()
    print("\n" + "━" * 50)
    print("  Cycle 4: Sarah returns (goal reinforcement)")
    print("━" * 50)
    pipeline.process(recognition_result)
    time.sleep(3)

    # ---- Cycle 5: Life Continuity & Daily Orientation ----
    pipeline.reset()
    print("\n" + "━" * 50)
    print("  Cycle 5: Life Continuity & Daily Orientation (Sarah Visit + Routine Stage)")
    print("━" * 50)
    pipeline.process(recognition_result)
    time.sleep(3)

    # ---- Cycle 6: Preserving Human Connections ----
    pipeline.reset()
    print("\n" + "━" * 50)
    print("  Cycle 6: Preserving Human Connections (Shared Memories & Relationship Card)")
    print("━" * 50)
    pipeline.process(recognition_result)
    time.sleep(3)

    print("\n✅ Scripted scenario complete. Dashboard is still live.")
    print("   Press Ctrl+C to exit.\n")


def run_camera_loop(pipeline: CognitivePipeline, db: MemoraDatabase):
    """
    Run the live camera loop (requires webcam).
    """
    import cv2
    from devices.camera import CameraDevice
    from devices.speaker import SpeakerDevice
    from src.audio.audio_listener import MemoraAudioListener
    from src.reasoning.context_binder import MemoraContextBinder
    from src.vision.face_recognizer import MemoraFaceRecognizer
    from src.coordinator.anchor_coordinator import AnchorCoordinator
    from src.runtime.runtime import AnchorRuntime

    camera = CameraDevice()
    if not camera.open():
        print("❌ Failed to open camera. Use --scenario for scripted demo.")
        return

    recognizer = MemoraFaceRecognizer(mock_mode=True)
    listener = MemoraAudioListener(mock_mode=True)
    binder = MemoraContextBinder()
    speaker = SpeakerDevice()

    coordinator = AnchorCoordinator(
        database=db,
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
            recognizer.draw_faces(frame, results)
            actions = coordinator.consume_actions()
            for action in actions:
                speaker.execute(action)
            cv2.imshow("Memora Live Feed", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        runtime.shutdown()
        camera.release()
        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="Memora Experience Platform")
    parser.add_argument("--no-camera", action="store_true", help="Run without camera")
    parser.add_argument("--scenario", action="store_true", help="Run scripted demo scenario")
    args = parser.parse_args()

    print("=" * 60)
    print("  🧠 Memora Experience Platform")
    print("  Samsung Anchor · Cognitive Architecture Demo")
    print("=" * 60)

    # Initialize database
    db = MemoraDatabase()
    db.clear()

    # Initialize pipeline
    pipeline = CognitivePipeline(db)
    pipeline.context_restoration_engine.client = MockReasoningClient()

    # Start Experience Server
    server = ExperienceServer()
    server.start()

    # Open dashboard
    server.open_dashboard()

    if args.scenario or args.no_camera:
        try:
            run_scripted_scenario(pipeline, db)
            # Keep server alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down Memora Experience Platform.")
    else:
        run_camera_loop(pipeline, db)


if __name__ == "__main__":
    main()
