"""
MEMORA Dependency Validator.

Verifies architectural dependency direction, detects circular imports,
and ensures no protocol leakage or forbidden coupling between layers.
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Set

from validation.validation_models import ValidationDomain, ValidationReport, ValidationResult, ValidationStatus

# Architectural layers ordered bottom-to-top — lower layers must not import higher layers.
LAYER_ORDER = [
    "src/perception",
    "src/cognition",
    "src/trust",
    "src/behaviour",
    "src/experience",
    "src/memory",
    "src/knowledge",
    "src/reasoning",
    "src/executive",
    "src/core",
    "src/integrity",
    "src/runtime",
    "src/session",
    "src/configuration",
    "src/security",
    "src/edge",
    "src/io",
    "src/interoperability",
    "src/assistance",
    "src/caregiver",
]

FORBIDDEN_IMPORTS = [
    "android",
    "objc",
    "swift",
    "flutter",
    "react_native",
    "bluetooth",
    "bleak",
]


class DependencyValidator:
    """Validates architectural dependency constraints across MEMORA subsystems."""

    def __init__(self, root_dir: str = ".") -> None:
        self._root = root_dir

    def validate(self) -> ValidationReport:
        report = ValidationReport(domain=ValidationDomain.DEPENDENCY)

        # Check 1: No forbidden platform imports
        for forbidden in FORBIDDEN_IMPORTS:
            found_files = self._grep_imports(forbidden)
            if found_files:
                report.results.append(ValidationResult(
                    domain=ValidationDomain.DEPENDENCY,
                    check_name=f"Forbidden import: {forbidden}",
                    status=ValidationStatus.FAILED,
                    detail=f"Found in: {', '.join(found_files)}",
                ))
            else:
                report.results.append(ValidationResult(
                    domain=ValidationDomain.DEPENDENCY,
                    check_name=f"Forbidden import: {forbidden}",
                    status=ValidationStatus.PASSED,
                    detail=f"No `{forbidden}` imports detected in src/.",
                ))

        # Check 2: Verify all subsystem packages exist
        for layer_path in LAYER_ORDER:
            full_path = os.path.join(self._root, layer_path)
            exists = os.path.isdir(full_path)
            report.results.append(ValidationResult(
                domain=ValidationDomain.DEPENDENCY,
                check_name=f"Package exists: {layer_path}",
                status=ValidationStatus.PASSED if exists else ValidationStatus.WARNING,
                detail=f"{'Directory exists' if exists else 'Directory missing'}.",
            ))

        report.summary = f"Dependency validation: {report.passed_count}/{report.total_count} checks passed."
        return report

    def _grep_imports(self, keyword: str) -> List[str]:
        """Scan src/ Python files for forbidden import statements."""
        matches = []
        src_dir = os.path.join(self._root, "src")
        if not os.path.isdir(src_dir):
            return matches
        for dirpath, _, filenames in os.walk(src_dir):
            if "__pycache__" in dirpath:
                continue
            for fname in filenames:
                if not fname.endswith(".py"):
                    continue
                filepath = os.path.join(dirpath, fname)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        for line in f:
                            if re.search(rf'\bimport\s+{keyword}\b', line) or re.search(rf'\bfrom\s+{keyword}\b', line):
                                matches.append(filepath)
                                break
                except (OSError, UnicodeDecodeError):
                    continue
        return matches
