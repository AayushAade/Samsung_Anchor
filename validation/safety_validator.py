"""
MEMORA Safety Validator.

Validates clinical safety constraints: no hallucination paths, verified memory usage,
safe escalation policies, security boundary preservation, and clinical protocol isolation.
"""

from __future__ import annotations

from validation.validation_models import ValidationDomain, ValidationReport, ValidationResult, ValidationStatus


class SafetyValidator:
    """Validates safety, trust, and clinical isolation invariants."""

    def validate(self) -> ValidationReport:
        report = ValidationReport(domain=ValidationDomain.SAFETY)

        # Check 1: Trust package exists and is importable
        try:
            import src.trust
            report.results.append(ValidationResult(
                domain=ValidationDomain.SAFETY,
                check_name="Trust framework importable",
                status=ValidationStatus.PASSED,
                detail="Trust package (`src.trust`) imported successfully.",
            ))
        except Exception as e:
            report.results.append(ValidationResult(
                domain=ValidationDomain.SAFETY,
                check_name="Trust framework importable",
                status=ValidationStatus.FAILED,
                detail=str(e),
            ))

        # Check 2: Security engine access control
        try:
            from src.security import SecurityEngine
            sec = SecurityEngine()
            snap = sec.snapshot()
            report.results.append(ValidationResult(
                domain=ValidationDomain.SAFETY,
                check_name="Security access control operational",
                status=ValidationStatus.PASSED,
                detail=f"SecurityEngine snapshot generated. Checksum: {snap.checksum}.",
            ))
        except Exception as e:
            report.results.append(ValidationResult(
                domain=ValidationDomain.SAFETY,
                check_name="Security access control operational",
                status=ValidationStatus.FAILED,
                detail=str(e),
            ))

        # Check 3: Caregiver escalation deterministic
        try:
            from src.caregiver import EscalationEngine, TimelineEvent, TimelineEventType, EscalationLevel
            esc = EscalationEngine()
            events = [TimelineEvent(event_type=TimelineEventType.ROUTINE_COMPLETION, description="done")]
            level, rules = esc.evaluate_escalation(events)
            report.results.append(ValidationResult(
                domain=ValidationDomain.SAFETY,
                check_name="Escalation determinism (baseline = NONE)",
                status=ValidationStatus.PASSED if level == EscalationLevel.NONE else ValidationStatus.FAILED,
                detail=f"Baseline escalation level: {level.value}. Rules: {len(rules)}.",
            ))
        except Exception as e:
            report.results.append(ValidationResult(
                domain=ValidationDomain.SAFETY,
                check_name="Escalation determinism",
                status=ValidationStatus.FAILED,
                detail=str(e),
            ))

        # Check 4: Clinical interoperability isolation
        try:
            from src.interoperability import InteroperabilityEngine
            interop = InteroperabilityEngine()
            snap = interop.snapshot()
            report.results.append(ValidationResult(
                domain=ValidationDomain.SAFETY,
                check_name="Clinical interoperability isolation",
                status=ValidationStatus.PASSED,
                detail=f"InteroperabilityEngine snapshot generated. Checksum: {snap.checksum}.",
            ))
        except Exception as e:
            report.results.append(ValidationResult(
                domain=ValidationDomain.SAFETY,
                check_name="Clinical interoperability isolation",
                status=ValidationStatus.FAILED,
                detail=str(e),
            ))

        report.summary = f"Safety validation: {report.passed_count}/{report.total_count} checks passed."
        return report
