#!/usr/bin/env python3
"""
MEMORA One-Command Pre-Demo Health Check CLI.

Usage:
    python health_check.py
"""

import sys
from src.operations.startup_validator import StartupValidator


def main() -> int:
    print("======================================================================")
    print("MEMORA (Samsung Anchor) — Pre-Demo Diagnostic Health Check")
    print("======================================================================")

    validator = StartupValidator()
    results = validator.run_all_checks()

    has_fail = False
    has_warning = False

    print(f"\n| {'Component':<28} | {'Status':<8} | {'Message':<45} |")
    print("| " + "-" * 28 + " | " + "-" * 8 + " | " + "-" * 45 + " |")

    for item in results:
        symbol = "✅ PASS" if item.status == "PASS" else ("⚠️ WARN" if item.status == "WARNING" else "❌ FAIL")
        print(f"| {item.component:<28} | {symbol:<8} | {item.message:<45} |")

        if item.status == "FAIL":
            has_fail = True
            print(f"   └── Remediation: {item.remediation}")
        elif item.status == "WARNING":
            has_warning = True

    print("\n----------------------------------------------------------------------")
    if has_fail:
        print("OVERALL DIAGNOSTIC RESULT: ❌ FAIL — Critical issues detected")
        print("----------------------------------------------------------------------\n")
        return 1
    elif has_warning:
        print("OVERALL DIAGNOSTIC RESULT: ⚠️ PASS WITH WARNINGS — Operational with fallbacks")
        print("----------------------------------------------------------------------\n")
        return 0
    else:
        print("OVERALL DIAGNOSTIC RESULT: ✅ PASS — System fully operational for live demo")
        print("----------------------------------------------------------------------\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
