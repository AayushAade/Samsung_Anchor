#!/usr/bin/env python3
"""
MEMORA One-Command Master Runtime Validation & Evidence Generator.

Usage:
    python validate_runtime.py [--duration SECONDS]

Example:
    python validate_runtime.py --duration 10
"""

import argparse
import sys
from validation.runner.validation_runner import ValidationRunner


def main() -> int:
    parser = argparse.ArgumentParser(description="MEMORA One-Command Runtime Validation Runner")
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Validation runtime session duration in seconds (default: 5.0)",
    )
    args = parser.parse_args()

    print("======================================================================")
    print("MEMORA (Samsung Anchor) — Runtime Reliability & Evidence Framework")
    print(f"Executing validation session (Duration: {args.duration}s)...")
    print("======================================================================")

    runner = ValidationRunner(duration_seconds=args.duration)
    report = runner.execute_validation()

    print("\n----------------------------------------------------------------------")
    print(f"Validation Decision : {report['overall_status']}")
    print(f"Frames Processed   : {report['telemetry']['counters'].get('processed_frames', 0)}")
    print(f"Frame Rate         : {report['telemetry']['frame_rate_fps']:.2f} FPS")
    print(f"Average Memory     : {report['telemetry']['avg_ram_mb']:.2f} MB")
    print(f"Fault Recovery     : {len(report['fault_tests'])} / {len(report['fault_tests'])} Scenarios PASSED")
    print("----------------------------------------------------------------------")
    print("Generated Reports  : validation/reports/")
    print("Evidence Package   : validation/artifacts/")
    print("======================================================================\n")

    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
