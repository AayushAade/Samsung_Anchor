#!/usr/bin/env python3
"""
MEMORA Demo Operator Interface CLI.

Provides simple operational controls for live demonstration, health diagnostics,
validation execution, and session export during presentations.

Usage:
    python operate.py [--health | --demo | --validate | --status | --export]
"""

import argparse
import sys
from src.operations.orchestrator import SystemOrchestrator
from src.operations.startup_validator import StartupValidator
from src.operations.session_recorder import SessionRecorder
from src.clinical.demo_mode import AutomaticDemoRunner
from validation.runner.validation_runner import ValidationRunner


def run_health() -> None:
    print("\n--- Running Pre-Demo Diagnostics ---")
    validator = StartupValidator()
    results = validator.run_all_checks()
    for r in results:
        symbol = "✅" if r.status == "PASS" else ("⚠️" if r.status == "WARNING" else "❌")
        print(f"{symbol} [{r.status}] {r.component}: {r.message}")


def run_demo() -> None:
    print("\n--- Executing Master Demo Mode ---")
    runner = AutomaticDemoRunner()
    runner.run_all_scenarios()


def run_validate() -> None:
    print("\n--- Executing Validation & Benchmark Suite ---")
    runner = ValidationRunner(duration_seconds=5.0)
    report = runner.execute_validation()
    print(f"Validation Status: {report['overall_status']}")
    print(f"Frame Rate: {report['telemetry']['frame_rate_fps']:.2f} FPS")


def view_status() -> None:
    print("\n--- System Orchestrator Subsystem Status ---")
    orchestrator = SystemOrchestrator()
    summary = orchestrator.get_system_health_summary()
    print(f"Overall Status: {summary['overall_status']} ({summary['healthy_count']}/{summary['total_subsystems']} Healthy)")
    for name, sub in summary["subsystems"].items():
        print(f"  • {name:<25} : [{sub['status']}] {sub['health_msg']} (Uptime: {sub['uptime_seconds']}s)")


def export_session() -> None:
    print("\n--- Exporting Demonstration Session Artifacts ---")
    recorder = SessionRecorder(session_name="Operator_Session")
    recorder.record_event("Demo", "Started demonstration session")
    recorder.record_event("Perception", "Face tracking active", {"status": "HEALTHY"})
    json_path, md_path = recorder.export_session()
    print(f"Exported JSON Log: {json_path}")
    print(f"Exported Markdown Log: {md_path}")


def interactive_menu() -> None:
    print("======================================================================")
    print("     MEMORA (Samsung Anchor) — DEMO OPERATOR CONTROL CONSOLE")
    print("======================================================================")
    print("1. Run Health Diagnostics (health_check)")
    print("2. Run Master Demo Mode (demo_mode)")
    print("3. Run Validation & Benchmarks (validate_runtime)")
    print("4. View Orchestrator Subsystem Status")
    print("5. Export Session Artifacts")
    print("6. Exit")
    print("======================================================================")

    choice = input("Select an option (1-6): ").strip()
    if choice == "1":
        run_health()
    elif choice == "2":
        run_demo()
    elif choice == "3":
        run_validate()
    elif choice == "4":
        view_status()
    elif choice == "5":
        export_session()
    else:
        print("Exiting operator control console.")


def main() -> int:
    parser = argparse.ArgumentParser(description="MEMORA Demo Operator Control Console")
    parser.add_argument("--health", action="store_true", help="Run health diagnostics")
    parser.add_argument("--demo", action="store_true", help="Run master demo mode")
    parser.add_argument("--validate", action="store_true", help="Run validation and benchmarks")
    parser.add_argument("--status", action="store_true", help="View orchestrator status")
    parser.add_argument("--export", action="store_true", help="Export demonstration session log")

    args = parser.parse_args()

    if args.health:
        run_health()
    elif args.demo:
        run_demo()
    elif args.validate:
        run_validate()
    elif args.status:
        view_status()
    elif args.export:
        export_session()
    else:
        interactive_menu()

    return 0


if __name__ == "__main__":
    sys.exit(main())
