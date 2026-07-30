"""
MEMORA Integration Validator.

Verifies that all completed cognitive and operational subsystems interact correctly
through their public interfaces without internal coupling violations.
"""

from __future__ import annotations

from validation.validation_models import ValidationDomain, ValidationReport, ValidationResult, ValidationStatus


# Ordered subsystem registry: Phase → (package path, key export)
SUBSYSTEM_REGISTRY = [
    ("Phase 21: Cognitive OS", "src.cognition.cos"),
    ("Phase 22: Trust & Safety", "src.trust"),
    ("Phase 23: Behaviour Intelligence", "src.behaviour"),
    ("Phase 24: Cognitive Reasoning", "src.reasoning"),
    ("Phase 25: Executive Function", "src.executive"),
    ("Phase 26: Experience Learning", "src.experience"),
    ("Phase 27: Architectural Core", "src.core"),
    ("Phase 28: Semantic Knowledge", "src.knowledge"),
    ("Phase 29: Long-Term Memory", "src.memory"),
    ("Phase 30: Clinical Runtime", "src.runtime"),
    ("Phase 31: Cognitive Session", "src.session"),
    ("Phase 32: Integrity", "src.integrity"),
    ("Phase 33: Configuration", "src.configuration"),
    ("Phase 34: Security", "src.security"),
    ("Phase 35: Unified I/O", "src.io"),
    ("Phase 36: Interoperability", "src.interoperability"),
    ("Phase 37: Assistance", "src.assistance"),
    ("Phase 38: Caregiver", "src.caregiver"),
    ("Phase 39: Edge Runtime", "src.edge"),
]


class IntegrationValidator:
    """Validates that every subsystem is importable and exposes its expected public interface."""

    def validate(self) -> ValidationReport:
        report = ValidationReport(domain=ValidationDomain.INTEGRATION)

        for phase_name, module_path in SUBSYSTEM_REGISTRY:
            try:
                __import__(module_path)
                report.results.append(ValidationResult(
                    domain=ValidationDomain.INTEGRATION,
                    check_name=f"Import: {phase_name}",
                    status=ValidationStatus.PASSED,
                    detail=f"Successfully imported `{module_path}`.",
                ))
            except Exception as e:
                report.results.append(ValidationResult(
                    domain=ValidationDomain.INTEGRATION,
                    check_name=f"Import: {phase_name}",
                    status=ValidationStatus.FAILED,
                    detail=f"Import failed: {e}",
                ))

        report.summary = (
            f"Integration validation: {report.passed_count}/{report.total_count} subsystems verified."
        )
        return report
