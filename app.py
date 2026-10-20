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


def configure_logging(verbose: bool = False) -> str:
    """
    Console: warnings and errors only (debug with --verbose).
    File: data/logs/memora.log, rotated at 5 MB x 3, owner-only because it can
    contain what the person said.
    """
    from logging.handlers import RotatingFileHandler
    from config.paths import DATA_DIR

    from pathlib import Path
    from config import settings
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "memora.log"
    if not log_path.exists():
        os.close(os.open(log_path, os.O_WRONLY | os.O_CREAT, 0o600))
    os.chmod(log_path, 0o600)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    for h in list(root.handlers):
        root.removeHandler(h)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG if verbose else logging.WARNING)
    console.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    file_handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=3)
    file_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root.addHandler(console)
    root.addHandler(file_handler)
    return str(log_path)
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
    if live_hardware is not True:
        print("🤖 OPERATIONAL MODE: SIMULATION (real devices are used only with --live-hardware)")
        print("   • Video Feed : Simulated Frame Generator")
        print("   • Audio Feed : Simulated Audio Listener")
        print("   • Speaker    : Console log only (no audio)")
        print(f"   • LLM Mode   : {llm_mode_str}")
    else:
        print("🎥 OPERATIONAL MODE: LIVE HARDWARE requested (--live-hardware); unavailable devices are reported below")
        print("   • Video Feed : OpenCV Camera Adapter (Index 0 / Fallback)")
        print("   • Audio Feed : PyAudio Microphone Adapter (Native / Fallback)")
        print("   • Speaker    : Text-to-Speech Engine (Native / Console Fallback)")
        print(f"   • LLM Mode   : {llm_mode_str}")
    print("=" * 60)

    # Synthetic sensors and scripted scenarios write synthetic faces/episodes.
    # Keep them out of the person's real memory database unless the operator
    # explicitly chose a database with MEMORA_DB_PATH.
    if (live_hardware is not True or run_scenarios) and not os.environ.get("MEMORA_DB_PATH"):
        from config import settings
        from config.paths import DATA_DIR
        settings.DB_PATH = str(DATA_DIR / "simulation" / "memora_simulation.sqlite")
        print(f"🧪 Simulation data is stored separately at: {settings.DB_PATH}")

    # Build application and initialize runtime
    from src.memory.database import DatabaseUnavailableError, open_user_database
    try:
        database = open_user_database()
    except DatabaseUnavailableError as e:
        print(e)
        sys.exit(2)
    coordinator = build_application(live_hardware=live_hardware, database=database)
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


def _configured_db_file() -> str:
    from config import settings
    from src.memory.database import resolve_db_url
    fs_path = resolve_db_url(settings.DB_PATH)[1]
    if fs_path is None:
        raise SystemExit("The configured database is in-memory; nothing to back up or restore.")
    return fs_path


def run_backup(dest: str) -> int:
    from src.memory.backup import BackupError, create_backup, verify_backup
    db_file = _configured_db_file()
    try:
        target = create_backup(db_file, dest)
        report = verify_backup(target)
    except (BackupError, OSError) as e:
        print(f"Backup FAILED: {e}")
        return 1
    rows = report["manifest"]["row_counts"]
    print(f"Backup written and verified: {target}")
    print(f"  people={rows.get('identities', 0)} facts/memories={rows.get('relevant_memories', 0)} "
          f"episodes={rows.get('episodes', 0)} care items={rows.get('care_items', 0)}")
    if not report["integrity"]["ok"]:
        print("  Note: the source database has integrity warnings (see `python app.py --check`).")
    return 0


def run_restore(backup_dir: str, read=input) -> int:
    from src.memory.backup import BackupError, restore_backup, verify_backup
    db_file = _configured_db_file()
    try:
        checked = verify_backup(backup_dir)
    except (BackupError, OSError, KeyError, ValueError) as e:
        print(f"Backup cannot be used: {e}")
        return 1
    m = checked["manifest"]
    print(f"Backup from {m['created_at']} (source {m['source_db']}), checksums OK.")
    print(f"This will REPLACE {db_file} and its face data. Stop any running MEMORA first.")
    if read("Type RESTORE to continue: ").strip() != "RESTORE":
        print("Cancelled. Nothing was changed.")
        return 0
    try:
        result = restore_backup(backup_dir, db_file)
    except (BackupError, OSError) as e:
        print(f"Restore FAILED: {e}")
        return 1
    print(f"Restored. Previous files saved to: {result['pre_restore_backup'] or '(none existed)'}")
    return 0


def run_repair(read=input) -> int:
    """
    Interactive repair of the configured database. Nothing is changed without
    the operator typing DELETE. A backup copy is made first.
    """
    import shutil
    from datetime import datetime
    from config import settings
    from src.memory.database import MemoraDatabase
    from src.memory import user_data

    db = MemoraDatabase(settings.DB_PATH)
    orphans = user_data.orphaned_identities(db)
    print(f"Database: {db.db_path}")
    if not orphans:
        print("No people records without face data. Nothing to repair.")
        return 0
    print(f"{len(orphans)} people records have no face data and cannot be recognised:")
    for p in orphans:
        print(f"  {p['id']:<18} name={p['name'] or '-':<14} relationship={p['relationship'] or '-':<12} last seen {p['last_seen'] or 'never'}")
    print("Facts, episodes and object sightings are NOT affected.")
    if read("Type DELETE to remove these records (a backup is made first): ").strip() != "DELETE":
        print("Cancelled. Nothing was changed.")
        return 0
    backup = f"{db.db_path}.backup-{datetime.now():%Y%m%d%H%M%S}"
    shutil.copy2(db.db_path, backup)
    os.chmod(backup, 0o600)
    result = user_data.delete_orphaned_identities(db)
    print(f"Backup written to {backup}")
    print(f"Deleted {len(result['deleted'])} records. Integrity check: {'OK' if result['integrity_ok'] else 'still inconsistent'}")
    return 0 if result["integrity_ok"] else 1


def cli():
    parser = argparse.ArgumentParser(description="MEMORA (Samsung Anchor) Cognitive Platform")
    parser.add_argument("--scenario", action="store_true", help="Run 10 clinical caregiving scenario validations")
    parser.add_argument("--dashboard", action="store_true", help="Launch live Experience Platform browser dashboard")
    parser.add_argument("--max-cycles", type=int, default=None, help="Maximum execution cycles (default: continuous)")
    parser.add_argument("--vision-standalone", action="store_true", help="Run standalone OpenCV vision detection and tracking loop")
    parser.add_argument("--show-memory", action="store_true", help="Print memory timeline, visitors, conversations, objects, facts, and DB stats")
    parser.add_argument("--verbose", action="store_true", help="Show debug diagnostics on the console")
    parser.add_argument("--check", action="store_true", help="Run diagnostics (dependencies, user database integrity, optional capabilities) without opening the camera; exit 1 on failure")
    parser.add_argument("--backup", nargs="?", const="backups", metavar="DIR", help="Write a verified backup of the configured database (default dir: ./backups)")
    parser.add_argument("--restore", metavar="BACKUP_DIR", help="Restore the configured database from a backup directory (stop MEMORA first; asks for confirmation)")
    parser.add_argument("--simulate", nargs="*", metavar="JOURNEY", help="Run deterministic simulated user journeys in isolated temporary storage (all if none named)")
    parser.add_argument("--repair", action="store_true", help="List people records that have no face data and, after typed confirmation, delete them")
    parser.add_argument("--chat", action="store_true", help="Talk to MEMORA by typing (camera and microphone off); manage stored memories")
    parser.add_argument("--validate-runtime", action="store_true", help="Run runtime stability monitoring and output measured Runtime Report")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--live-hardware", action="store_true", help="Use the physical camera, microphone and speaker (the only way to enable real devices; MEMORA_PROFILE selects the hardware profile)")
    mode_group.add_argument("--simulation", action="store_true", help="Run in simulated mode with synthetic perception")

    args = parser.parse_args()
    configure_logging(verbose=args.verbose)

    if args.show_memory:
        show_memory_timeline()
        return

    if args.check:
        from health_check import main as run_health_check
        sys.exit(run_health_check(include_camera=False))

    if args.simulate is not None:
        from src.simulation.journeys import print_report, run_all
        sys.exit(print_report(run_all(args.simulate or None)))

    if args.backup is not None:
        sys.exit(run_backup(args.backup))

    if args.restore:
        sys.exit(run_restore(args.restore))

    if args.repair:
        sys.exit(run_repair())

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
        configure_logging()
        main(max_cycles=None)
