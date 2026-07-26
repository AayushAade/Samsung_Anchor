"""
Samsung Anchor Application

Official application entry point.

Responsibilities
----------------
- Build the Samsung Anchor application.
- Create the application runtime.
- Start the runtime.

Business logic belongs in the Coordinator.
Subsystem construction belongs in the Application Factory.
"""

from __future__ import annotations

import argparse
import signal
import sys
from typing import Optional

from src.application.factory import build_application
from src.runtime.runtime import AnchorRuntime
from src.clinical.scenario_validator import ClinicalScenarioValidator


def main(
    max_cycles: Optional[int] = 0,
    run_scenarios: bool = False,
    start_dashboard: bool = False,
    live_hardware: bool = False,
) -> None:
    """
    Samsung Anchor entry point.
    Runs continuous perception-cognition execution loop, scenario demonstrations, or dashboard server.
    """

    print("=" * 60)
    print("🧠 Samsung Anchor")
    print("Application Starting...")
    print("============================================================")
    if live_hardware:
        print("🎥 OPERATIONAL MODE: LIVE HARDWARE ACTIVE")
        print("   • Video Feed : OpenCV Camera Adapter (Index 0)")
        print("   • Audio Feed : Native PyAudio Microphone Adapter")
        print("   • Speaker    : Local Native TTS Engine")
    else:
        print("🤖 OPERATIONAL MODE: SIMULATION DEMONSTRATION ACTIVE")
        print("   • Video Feed : Simulated Frame Generator")
        print("   • Audio Feed : Simulated Audio Listener")
        print("   • Speaker    : Console Audio Dispatch Log")
    print("=" * 60)

    # Build application and initialize runtime
    coordinator = build_application(live_hardware=live_hardware)
    runtime = AnchorRuntime(coordinator)
    runtime.initialize()

    print("Application factory ready.")
    print("Runtime integration ready.")
    print("System initialization complete.")
    print("Samsung Anchor is ready for runtime execution.")

    # Phase 6 Observability Status Report
    statuses = runtime.get_subsystem_statuses()
    print("\n" + "=" * 60)
    print("📊 MEMORA Subsystem Observability Status")
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

    # Signal handler for graceful Ctrl+C / SIGINT / SIGTERM shutdown
    def handle_signal(sig, frame):
        print("\n🛑 Shutdown signal received. Gracefully stopping MEMORA Runtime...")
        runtime.shutdown()
        sys.exit(0)

    try:
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
    except (ValueError, OSError):
        # Handle cases where signal registration fails (e.g. non-main thread in tests)
        pass

    # In interactive CLI mode, run continuous loop unless max_cycles is explicitly 0
    if max_cycles != 0:
        runtime.start()
        runtime.run_continuous(max_cycles=max_cycles, cycle_delay=0.1)


def cli():
    parser = argparse.ArgumentParser(description="MEMORA (Samsung Anchor) Cognitive Platform")
    parser.add_argument("--scenario", action="store_true", help="Run 10 clinical caregiving scenario validations")
    parser.add_argument("--dashboard", action="store_true", help="Launch live Experience Platform browser dashboard")
    parser.add_argument("--max-cycles", type=int, default=None, help="Maximum execution cycles (default: continuous)")
    
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--live-hardware", action="store_true", help="Enforce physical camera, microphone, and TTS HAL")
    mode_group.add_argument("--simulation", action="store_true", help="Run in simulated mode with synthetic perception")

    args = parser.parse_args()

    main(
        max_cycles=args.max_cycles,
        run_scenarios=args.scenario,
        start_dashboard=args.dashboard,
        live_hardware=args.live_hardware,
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli()
    else:
        main(max_cycles=None)