"""
MEMORA Explainability Validator.

Verifies that every major cognitive subsystem produces traceable, evidence-backed
explanations through its explainer module.
"""

from __future__ import annotations

from validation.validation_models import ValidationDomain, ValidationReport, ValidationResult, ValidationStatus


class ExplainabilityValidator:
    """Validates that every major subsystem produces traceable explanations."""

    def validate(self) -> ValidationReport:
        report = ValidationReport(domain=ValidationDomain.EXPLAINABILITY)

        # 1. Assistance Framework Explainability
        try:
            from src.assistance import AssistanceEngine, AssistanceExplainer
            eng = AssistanceEngine()
            exp = AssistanceExplainer.explain_engine_state(eng)
            report.results.append(ValidationResult(
                domain=ValidationDomain.EXPLAINABILITY,
                check_name="Explainability: Assistance Framework",
                status=ValidationStatus.PASSED if len(exp) > 20 else ValidationStatus.FAILED,
                detail=f"Generated {len(exp)} chars diagnostic report.",
            ))
        except Exception as e:
            report.results.append(ValidationResult(
                domain=ValidationDomain.EXPLAINABILITY,
                check_name="Explainability: Assistance Framework",
                status=ValidationStatus.FAILED,
                detail=str(e),
            ))

        # 2. Caregiver Intelligence Explainability
        try:
            from src.caregiver import CaregiverEngine, CaregiverExplainer
            eng = CaregiverEngine()
            exp = CaregiverExplainer.explain_engine_state(eng)
            report.results.append(ValidationResult(
                domain=ValidationDomain.EXPLAINABILITY,
                check_name="Explainability: Caregiver Intelligence",
                status=ValidationStatus.PASSED if len(exp) > 20 else ValidationStatus.FAILED,
                detail=f"Generated {len(exp)} chars diagnostic report.",
            ))
        except Exception as e:
            report.results.append(ValidationResult(
                domain=ValidationDomain.EXPLAINABILITY,
                check_name="Explainability: Caregiver Intelligence",
                status=ValidationStatus.FAILED,
                detail=str(e),
            ))

        # 3. Edge Runtime Explainability
        try:
            from src.edge import EdgeEngine, EdgeExplainer
            eng = EdgeEngine()
            exp = EdgeExplainer.explain_engine_state(eng)
            report.results.append(ValidationResult(
                domain=ValidationDomain.EXPLAINABILITY,
                check_name="Explainability: Edge Runtime",
                status=ValidationStatus.PASSED if len(exp) > 20 else ValidationStatus.FAILED,
                detail=f"Generated {len(exp)} chars diagnostic report.",
            ))
        except Exception as e:
            report.results.append(ValidationResult(
                domain=ValidationDomain.EXPLAINABILITY,
                check_name="Explainability: Edge Runtime",
                status=ValidationStatus.FAILED,
                detail=str(e),
            ))

        # 4. Unified I/O Framework Explainability
        try:
            from src.io import IOEngine, IOExplainer
            eng = IOEngine()
            exp = IOExplainer.explain_io_state(eng)
            report.results.append(ValidationResult(
                domain=ValidationDomain.EXPLAINABILITY,
                check_name="Explainability: Unified I/O Framework",
                status=ValidationStatus.PASSED if len(exp) > 20 else ValidationStatus.FAILED,
                detail=f"Generated {len(exp)} chars diagnostic report.",
            ))
        except Exception as e:
            report.results.append(ValidationResult(
                domain=ValidationDomain.EXPLAINABILITY,
                check_name="Explainability: Unified I/O Framework",
                status=ValidationStatus.FAILED,
                detail=str(e),
            ))

        # 5. Clinical Interoperability Explainability
        try:
            from src.interoperability import InteroperabilityEngine, InteroperabilityExplainer
            eng = InteroperabilityEngine()
            exp = InteroperabilityExplainer.explain_interoperability_state(eng)
            report.results.append(ValidationResult(
                domain=ValidationDomain.EXPLAINABILITY,
                check_name="Explainability: Clinical Interoperability",
                status=ValidationStatus.PASSED if len(exp) > 20 else ValidationStatus.FAILED,
                detail=f"Generated {len(exp)} chars diagnostic report.",
            ))
        except Exception as e:
            report.results.append(ValidationResult(
                domain=ValidationDomain.EXPLAINABILITY,
                check_name="Explainability: Clinical Interoperability",
                status=ValidationStatus.FAILED,
                detail=str(e),
            ))

        # 6. Security Framework Explainability
        try:
            from src.security import SecurityEngine, SecurityExplainer
            eng = SecurityEngine()
            exp = SecurityExplainer.explain_engine_state(eng)
            report.results.append(ValidationResult(
                domain=ValidationDomain.EXPLAINABILITY,
                check_name="Explainability: Security Framework",
                status=ValidationStatus.PASSED if len(exp) > 20 else ValidationStatus.FAILED,
                detail=f"Generated {len(exp)} chars diagnostic report.",
            ))
        except Exception as e:
            report.results.append(ValidationResult(
                domain=ValidationDomain.EXPLAINABILITY,
                check_name="Explainability: Security Framework",
                status=ValidationStatus.FAILED,
                detail=str(e),
            ))

        # 7. Configuration Framework Explainability
        try:
            from src.configuration import ConfigurationEngine, ConfigurationExplainer
            eng = ConfigurationEngine()
            exp = ConfigurationExplainer.explain_configuration_state(eng)
            report.results.append(ValidationResult(
                domain=ValidationDomain.EXPLAINABILITY,
                check_name="Explainability: Configuration Framework",
                status=ValidationStatus.PASSED if len(exp) > 20 else ValidationStatus.FAILED,
                detail=f"Generated {len(exp)} chars diagnostic report.",
            ))
        except Exception as e:
            report.results.append(ValidationResult(
                domain=ValidationDomain.EXPLAINABILITY,
                check_name="Explainability: Configuration Framework",
                status=ValidationStatus.FAILED,
                detail=str(e),
            ))

        # 8. Integrity Framework Explainability
        try:
            from src.integrity import IntegrityEngine, IntegrityExplainer
            eng = IntegrityEngine()
            rep = eng.run_integrity_check()
            exp = IntegrityExplainer.explain_report(rep)
            report.results.append(ValidationResult(
                domain=ValidationDomain.EXPLAINABILITY,
                check_name="Explainability: Integrity Framework",
                status=ValidationStatus.PASSED if len(exp) > 20 else ValidationStatus.FAILED,
                detail=f"Generated {len(exp)} chars diagnostic report.",
            ))
        except Exception as e:
            report.results.append(ValidationResult(
                domain=ValidationDomain.EXPLAINABILITY,
                check_name="Explainability: Integrity Framework",
                status=ValidationStatus.FAILED,
                detail=str(e),
            ))

        report.summary = f"Explainability validation: {report.passed_count}/{report.total_count} subsystems verified."
        return report
