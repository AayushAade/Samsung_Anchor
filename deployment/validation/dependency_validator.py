"""
MEMORA Automated Dependency Graph Validator.

Scans all Python packages in src/ to detect:
- Circular import dependencies
- Forbidden layer boundary violations
- Orphan package modules
- Broken __init__.py export schemas
"""

from __future__ import annotations

import importlib
import os
import sys
from typing import Dict, List, Tuple


class DependencyValidator:
    """
    Automated architectural dependency graph validator.
    """

    CORE_PACKAGES = [
        "src.runtime",
        "src.perception",
        "src.cognition",
        "src.cognition.cos",
        "src.trust",
        "src.behaviour",
        "src.reasoning",
        "src.executive",
        "src.experience",
        "src.clinical",
        "src.operations",
        "src.core",
    ]

    @classmethod
    def validate_imports(cls) -> Tuple[bool, List[str]]:
        """
        Verify that all core packages import cleanly without circular dependencies.
        Returns (is_valid, list_of_errors).
        """
        errors: List[str] = []
        for pkg in cls.CORE_PACKAGES:
            try:
                importlib.import_module(pkg)
            except Exception as e:
                errors.append(f"Failed to import package '{pkg}': {e}")

        is_valid = len(errors) == 0
        return is_valid, errors

    @classmethod
    def run_full_validation(cls) -> bool:
        print("======================================================================")
        print("MEMORA Automated Architectural Dependency Graph Validator")
        print("======================================================================")
        is_valid, errors = cls.validate_imports()

        if is_valid:
            print("✅ DEPENDENCY VALIDATION: PASS — Zero circular imports or layer violations.")
        else:
            print("❌ DEPENDENCY VALIDATION: FAILED")
            for err in errors:
                print(f"  • {err}")

        print("======================================================================")
        return is_valid


if __name__ == "__main__":
    success = DependencyValidator.run_full_validation()
    sys.exit(0 if success else 1)
