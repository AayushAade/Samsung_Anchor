#!/usr/bin/env python3
"""
MEMORA One-Command Automatic Demonstration Runner.

Usage:
    python demo_mode.py
"""

import sys
from src.clinical.demo_mode import AutomaticDemoRunner


def main() -> int:
    runner = AutomaticDemoRunner()
    res = runner.run_all_scenarios()
    return 0 if res["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
