"""
Samsung Anchor Application

Official application entry point.

Responsibilities
----------------
- Build the Samsung Anchor application.
- Create the application runtime.
- Start the runtime or standalone vision processing loop.

Business logic belongs in the Coordinator.
Subsystem construction belongs in the Application Factory.
"""

from __future__ import annotations

import os

os.environ["ORT_LOGGING_LEVEL"] = "3"
os.environ["OPENCV_LOG_LEVEL"] = "OFF"

import argparse
import logging
import signal
import sys
import warnings
from typing import Optional

logging.getLogger("onnxruntime").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

from src.application.factory import build_application
from src.runtime.runtime import AnchorRuntime
from src.clinical.scenario_validator import ClinicalScenarioValidator


def run_vision_standalone_loop() -> None:
    """
    Standalone computer vision loop (from main branch).
    Captures live frame feed from webcam, detects faces, tracks IDs,
    and extracts embeddings using FaceDetector, FaceRecognizer, and FaceTracker.
    """
    try:
        import cv2
        from src.vision.detector import FaceDetector
        from src.vision.recognizer import FaceRecognizer
        from src.vision.tracker import FaceTracker
    except ImportError as e:
        print(f"❌ Failed to import vision modules for standalone mode: {e}")
        sys.exit(1)

    try:
        detector = FaceDetector()
        recognizer = FaceRecognizer()
        tracker = FaceTracker()
    except Exception as e:
        print(f"❌ Vision pipeline initialization error: {e}")
        sys.exit(1)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open camera device index 0.")
        sys.exit(1)

    print("🎥 Camera Started (Standalone Vision Pipeline)")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            detections = detector.detect(frame)
            if detections:
                tracked_detections = tracker.update(detections)

                for det in tracked_detections:
                    bbox = det["bbox"]
                    face_crop = frame[bbox[1]:bbox[3], bbox[0]:bbox[2]]

                    print("Detected Face")
                    identity, distance = recognizer.recognize(face_crop)
                    print("Embedding Generated")
                    print(f"Identity : {identity}")
                    print(f"Distance : {distance:.2f}")

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass


def main(
    max_cycles: Optional[int] = 0,
    run_scenarios: bool = False,
    start_dashboard: bool = False,
    live_hardware: Optional[bool] = None,
    vision_standalone: bool = False,
    validate_runtime: bool = False,
) -> None:
    """
    Samsung Anchor entry point.
    Runs continuous perception-cognition execution loop, scenario demonstrations, or standalone vision loop.
    """

    if vision_standalone:
        run_vision_standalone_loop()
        return

    print("=" * 60)
    print("🧠 Samsung Anchor")
    print("Application Starting...")
    print("============================================================")
    llm_active = bool(os.environ.get("GEMINI_API_KEY"))
    # Replies are produced by deterministic local rules. Gemini, when configured, is
    # only used to extract names during identity learning.
    llm_mode_str = ("Local rules for replies; Gemini (key set, unverified) for identity-learning name extraction"
                    if llm_active else "Local rules only (no cloud model configured)")
    if live_hardware is False:
        print("🤖 OPERATIONAL MODE: SIMULATION DEMONSTRATION ACTIVE")
        print("   • Video Feed : Simulated Frame Generator")
        print("   • Audio Feed : Simulated Audio Listener")
        print("   • Speaker    : Console log only (no audio)")
        print(f"   • LLM Mode   : {llm_mode_str}")
    else:
        print("🎥 OPERATIONAL MODE: LIVE HARDWARE (AUTO-DETECT / FALLBACK ACTIVE)")
        print("   • Video Feed : OpenCV Camera Adapter (Index 0 / Fallback)")
        print("   • Audio Feed : PyAudio Microphone Adapter (Native / Fallback)")
        print("   • Speaker    : Text-to-Speech Engine (Native / Console Fallback)")
        print(f"   • LLM Mode   : {llm_mode_str}")
    print("=" * 60)

    # Synthetic sensors and scripted scenarios write synthetic faces/episodes.
    # Keep them out of the person's real memory database unless the operator
    # explicitly chose a database with MEMORA_DB_PATH.
    if (live_hardware is False or run_scenarios) and not os.environ.get("MEMORA_DB_PATH"):
        from config import settings
        from config.paths import DATA_DIR
        settings.DB_PATH = str(DATA_DIR / "simulation" / "memora_simulation.sqlite")
        print(f"🧪 Simulation data is stored separately at: {settings.DB_PATH}")

    # Build application and initialize runtime
    coordinator = build_application(live_hardware=live_hardware)
    runtime = AnchorRuntime(coordinator)
    runtime.initialize()

    # Print MEMORA HARDWARE DIAGNOSTIC REPORT
    runtime.print_diagnostic_report()

    print("Application factory ready.")
    print("Runtime integration ready.")
    print("System initialization complete.")
    print("Samsung Anchor is ready for runtime execution.")

    # Phase 6 Observability Status Report & Operational State Determination
    statuses = runtime.get_subsystem_statuses()
    is_pure_live = all(s == "READY" for s in statuses.values())

    print("\n" + "=" * 60)
    if is_pure_live and live_hardware is not False:
        print("🟢 STATE A: LIVE HARDWARE MODE (all checked subsystems report READY)")
    else:
        print("🟡 STATE B: SIMULATED OR DEGRADED (see per-subsystem status below)")
    print("=" * 60)
    for subsystem, status in statuses.items():
        symbol = "✓" if "READY" in status else ("⚠️" if "WARNING" in status else "❌")
        print(f" {symbol} {subsystem:<20} : {status}")
    print("=" * 60 + "\n")

    # Launch Experience Platform Dashboard if requested
    if start_dashboard:
        try:
            from experience.server import ExperienceServer
            server = ExperienceServer()
            server.start()
            server.open_dashboard()
            print("🌐 Experience Platform Dashboard active at http://localhost:8765\n")
        except Exception as e:
            print(f"⚠️ [Dashboard Notice] Failed to start experience dashboard: {e}\n")

    # Run Clinical Scenario Demonstration Mode if requested
    if run_scenarios:
        print("🎬 Running 10 End-to-End Clinical Caregiving Scenarios...\n")
        from src.clinical.scenario_validator import get_all_clinical_scenario_specs
        specs = get_all_clinical_scenario_specs()
        validator = ClinicalScenarioValidator(coordinator.pipeline)
        results = validator.run_all_scenarios(specs)
        validator.print_scenario_summary(results)
        return

    # Phase 11 — Objective 2: Runtime Validation Mode
    if validate_runtime:
        print("⏱️ RUNNING LONG RUNTIME STABILITY VALIDATION...")
        from src.monitoring.memory_leak_detector import MemoryLeakDetector
        from src.monitoring.latency_profiler import PipelineLatencyProfiler
        import time

        detector = MemoryLeakDetector()
        profiler = PipelineLatencyProfiler.get_instance()
        start_t = time.time()

        cycles_to_run = max_cycles if max_cycles and max_cycles > 0 else 25
        print(f"Running {cycles_to_run} continuous perception-cognition execution cycles...")

        def _row_counts():
            db = coordinator.database
            return {"episodes": db.episode_repo.count(),
                    "memories": len(db.memory_repo.find_explicit()),
                    "objects": len(db.object_repo.get_all_objects())}

        rows_before = _row_counts()
        runtime.start()
        runtime.run_continuous(max_cycles=cycles_to_run, cycle_delay=0.05)
        duration = round(time.time() - start_t, 2)
        rows_after = _row_counts()

        health = detector.check_leaks()
        latencies = profiler.get_full_report()
        rm = getattr(coordinator.pipeline, "runtime_manager", None)
        cam = getattr(rm, "camera", None)
        mic = getattr(rm, "microphone", None)

        def _counter(dev, attr):
            return getattr(dev, attr) if dev is not None and hasattr(dev, attr) else "not tracked"

        print("\n" + "=" * 70)
        print("📊 MEMORA RUNTIME VALIDATION REPORT (measured in this run)")
        print("=" * 70)
        print(f"  • Runtime Duration    : {duration} s")
        print(f"  • Cycles Run          : {runtime.cycle_count}")
        print(f"  • Average Cycle Rate  : {round(runtime.cycle_count / max(0.1, duration), 2)} cycles/s")
        print(f"  • Heap RAM Usage      : {health['current_memory_mb']:.2f} MB (Peak: {health['peak_memory_mb']:.2f} MB)")
        print(f"  • Active Thread Count : {health['thread_count']}")
        print(f"  • Camera Source       : {type(cam).__name__ if cam else 'none'} | dropped frames: {_counter(cam, 'dropped_frames')}")
        print(f"  • Microphone Source   : {type(mic).__name__ if mic else 'none'}")
        print(f"  • Dropped Cognitive Events : {coordinator.dropped_events_count}")
        for key in rows_before:
            print(f"  • New {key:<17}: {rows_after[key] - rows_before[key]}")
        print("  • Note: a short run with simulated sensors is not evidence of long-duration")
        print("    stability or of real camera/microphone behaviour.")
        print("=" * 70 + "\n")

        detector.print_resource_report()
        profiler.print_summary()
        runtime.shutdown()
        return

    # Signal handler for graceful Ctrl+C / SIGINT / SIGTERM shutdown
    def handle_signal(sig, frame):
        print("\n🛑 Shutdown signal received. Gracefully stopping MEMORA Runtime...")
        runtime.shutdown()
        sys.exit(0)

    try:
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
    except (ValueError, OSError):
        pass

    if max_cycles != 0:
        runtime.start()
        runtime.run_continuous(max_cycles=max_cycles, cycle_delay=0.1)


def show_memory_timeline() -> None:
    """
    Objective 4: CLI Memory Timeline Viewer.
    Prints today's timeline, recent visitors, conversations, objects, facts, and DB stats.
    """
    from inspect_database import inspect_database
    inspect_database(None)  # configured default: settings.DB_PATH / MEMORA_DB_PATH


def cli():
    parser = argparse.ArgumentParser(description="MEMORA (Samsung Anchor) Cognitive Platform")
    parser.add_argument("--scenario", action="store_true", help="Run 10 clinical caregiving scenario validations")
    parser.add_argument("--dashboard", action="store_true", help="Launch live Experience Platform browser dashboard")
    parser.add_argument("--max-cycles", type=int, default=None, help="Maximum execution cycles (default: continuous)")
    parser.add_argument("--vision-standalone", action="store_true", help="Run standalone OpenCV vision detection and tracking loop")
    parser.add_argument("--show-memory", action="store_true", help="Print memory timeline, visitors, conversations, objects, facts, and DB stats")
    parser.add_argument("--chat", action="store_true", help="Talk to MEMORA by typing (camera and microphone off); manage stored memories")
    parser.add_argument("--validate-runtime", action="store_true", help="Run runtime stability monitoring and output measured Runtime Report")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--live-hardware", action="store_true", help="Enforce physical camera, microphone, and TTS HAL")
    mode_group.add_argument("--simulation", action="store_true", help="Run in simulated mode with synthetic perception")

    args = parser.parse_args()

    if args.show_memory:
        show_memory_timeline()
        return

    if args.chat:
        from src.application.chat import run_chat
        run_chat()
        return

    live_hw = None
    if args.live_hardware:
        live_hw = True
    elif args.simulation:
        live_hw = False

    main(
        max_cycles=args.max_cycles,
        run_scenarios=args.scenario,
        start_dashboard=args.dashboard,
        live_hardware=live_hw,
        vision_standalone=args.vision_standalone,
        validate_runtime=args.validate_runtime,
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli()
    else:
        main(max_cycles=None)
