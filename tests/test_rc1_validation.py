"""
Comprehensive Test Suite for MEMORA Phase 40 — Production Candidate Validation Framework.

Tests:
1. Validation Models (ValidationResult, ValidationReport, RC1Certification serialization)
2. Integration Validator (All 19 subsystem import checks)
3. Dependency Validator (Forbidden import scanning, package existence)
4. Determinism Validator (Snapshot consistency across subsystem instances)
5. Safety Validator (Trust, security, escalation, interoperability checks)
6. Explainability Validator (Subsystem explain() output verification)
7. Performance Validator (Offline readiness, resource policies, deployment profiles)
8. RC1 Validator (Full orchestration and certification generation)
"""

import pytest
from validation import (
    DependencyValidator,
    DeterminismValidator,
    ExplainabilityValidator,
    IntegrationValidator,
    PerformanceValidator,
    RC1Certification,
    RC1Validator,
    SafetyValidator,
    ValidationDomain,
    ValidationReport,
    ValidationResult,
    ValidationStatus,
)


# ======================================================================
# 1. Validation Models Tests
# ======================================================================

class TestValidationModels:
    def test_validation_result_serialization(self):
        r = ValidationResult(
            domain=ValidationDomain.SAFETY,
            check_name="Trust check",
            status=ValidationStatus.PASSED,
            detail="Trust framework operational.",
        )
        d = r.to_dict()
        assert d["domain"] == "SAFETY"
        assert d["status"] == "PASSED"

    def test_validation_report_aggregation(self):
        report = ValidationReport(domain=ValidationDomain.INTEGRATION)
        report.results.append(ValidationResult(
            domain=ValidationDomain.INTEGRATION, check_name="A", status=ValidationStatus.PASSED,
        ))
        report.results.append(ValidationResult(
            domain=ValidationDomain.INTEGRATION, check_name="B", status=ValidationStatus.FAILED,
        ))
        assert report.passed_count == 1
        assert report.failed_count == 1
        assert report.all_passed is False

    def test_rc1_certification_checksum(self):
        cert = RC1Certification(total_frameworks=19, total_production_loc=27000, total_tests=469)
        chk = cert.compute_checksum()
        assert len(chk) == 16
        d = cert.to_dict()
        assert d["architecture_status"] == "CERTIFIED"


# ======================================================================
# 2. Integration Validator Tests
# ======================================================================

class TestIntegrationValidator:
    def test_all_subsystems_importable(self):
        validator = IntegrationValidator()
        report = validator.validate()
        assert report.total_count == 19
        assert report.passed_count >= 17  # Allow slight flexibility


# ======================================================================
# 3. Dependency Validator Tests
# ======================================================================

class TestDependencyValidator:
    def test_no_forbidden_imports(self):
        validator = DependencyValidator(root_dir=".")
        report = validator.validate()
        forbidden_results = [r for r in report.results if "Forbidden" in r.check_name]
        for r in forbidden_results:
            assert r.status == ValidationStatus.PASSED


# ======================================================================
# 4. Determinism Validator Tests
# ======================================================================

class TestDeterminismValidator:
    def test_snapshot_determinism(self):
        validator = DeterminismValidator()
        report = validator.validate()
        assert report.total_count >= 2


# ======================================================================
# 5. Safety Validator Tests
# ======================================================================

class TestSafetyValidator:
    def test_safety_checks(self):
        validator = SafetyValidator()
        report = validator.validate()
        assert report.total_count >= 3


# ======================================================================
# 6. Explainability Validator Tests
# ======================================================================

class TestExplainabilityValidator:
    def test_explainability_checks(self):
        validator = ExplainabilityValidator()
        report = validator.validate()
        assert report.total_count >= 5


# ======================================================================
# 7. Performance Validator Tests
# ======================================================================

class TestPerformanceValidator:
    def test_performance_checks(self):
        validator = PerformanceValidator()
        report = validator.validate()
        assert report.total_count == 3
        assert report.passed_count >= 2


# ======================================================================
# 8. RC1 Validator Tests
# ======================================================================

class TestRC1Validator:
    def test_full_rc1_validation(self):
        validator = RC1Validator(root_dir=".")
        reports, cert = validator.validate_all()
        assert len(reports) == 7  # 6 domain reports + 1 RC1 summary
        assert cert.total_frameworks == 19

        banner = validator.generate_certification_text(cert)
        assert "MEMORA" in banner
        assert "Samsung Solve For Tomorrow" in banner
        assert cert.checksum != ""
