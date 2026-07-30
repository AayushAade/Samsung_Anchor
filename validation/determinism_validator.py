"""
MEMORA Determinism Validator.

Verifies that MEMORA subsystems produce identical outputs for identical inputs,
confirming snapshot consistency, configuration stability, and replay readiness.
"""

from __future__ import annotations

from validation.validation_models import ValidationDomain, ValidationReport, ValidationResult, ValidationStatus


class DeterminismValidator:
    """Validates deterministic behaviour across MEMORA subsystems."""

    def validate(self) -> ValidationReport:
        report = ValidationReport(domain=ValidationDomain.DETERMINISM)

        # Check 1: Edge engine snapshot determinism
        try:
            from src.edge import EdgeEngine
            e1 = EdgeEngine()
            s1 = e1.snapshot()
            e2 = EdgeEngine()
            s2 = e2.snapshot()
            match = s1.checksum == s2.checksum
            report.results.append(ValidationResult(
                domain=ValidationDomain.DETERMINISM,
                check_name="Edge snapshot determinism",
                status=ValidationStatus.PASSED if match else ValidationStatus.FAILED,
                detail=f"Checksums {'match' if match else 'diverge'}: {s1.checksum} vs {s2.checksum}.",
            ))
        except Exception as e:
            report.results.append(ValidationResult(
                domain=ValidationDomain.DETERMINISM,
                check_name="Edge snapshot determinism",
                status=ValidationStatus.FAILED,
                detail=str(e),
            ))

        # Check 2: Configuration registry determinism
        try:
            from src.configuration import ConfigurationEngine
            c1 = ConfigurationEngine()
            snap1 = c1.snapshot()
            c2 = ConfigurationEngine()
            snap2 = c2.snapshot()
            match = snap1.checksum == snap2.checksum
            report.results.append(ValidationResult(
                domain=ValidationDomain.DETERMINISM,
                check_name="Configuration snapshot determinism",
                status=ValidationStatus.PASSED if match else ValidationStatus.FAILED,
                detail=f"Checksums {'match' if match else 'diverge'}.",
            ))
        except Exception as e:
            report.results.append(ValidationResult(
                domain=ValidationDomain.DETERMINISM,
                check_name="Configuration snapshot determinism",
                status=ValidationStatus.FAILED,
                detail=str(e),
            ))

        # Check 3: Caregiver escalation determinism
        try:
            from src.caregiver import EscalationEngine, TimelineEvent, TimelineEventType, EscalationLevel
            esc1 = EscalationEngine()
            esc2 = EscalationEngine()
            events = [TimelineEvent(event_type=TimelineEventType.ROUTINE_COMPLETION, description="test")]
            level1, _ = esc1.evaluate_escalation(events)
            level2, _ = esc2.evaluate_escalation(events)
            match = level1 == level2
            report.results.append(ValidationResult(
                domain=ValidationDomain.DETERMINISM,
                check_name="Escalation policy determinism",
                status=ValidationStatus.PASSED if match else ValidationStatus.FAILED,
                detail=f"Escalation levels {'match' if match else 'diverge'}: {level1.value} vs {level2.value}.",
            ))
        except Exception as e:
            report.results.append(ValidationResult(
                domain=ValidationDomain.DETERMINISM,
                check_name="Escalation policy determinism",
                status=ValidationStatus.FAILED,
                detail=str(e),
            ))

        report.summary = f"Determinism validation: {report.passed_count}/{report.total_count} checks passed."
        return report
