"""
MEMORA Performance Validator.

Architectural performance readiness validation only — no benchmarking.
Verifies offline operation readiness, resource-aware deployment assumptions,
and edge execution portability.
"""

from __future__ import annotations

from validation.validation_models import ValidationDomain, ValidationReport, ValidationResult, ValidationStatus


class PerformanceValidator:
    """Validates architectural performance readiness without executing benchmarks."""

    def validate(self) -> ValidationReport:
        report = ValidationReport(domain=ValidationDomain.PERFORMANCE)

        # Check 1: Edge offline execution readiness
        try:
            from src.edge import EdgeEngine, RuntimeState
            engine = EdgeEngine()
            engine.activate_profile("OFFLINE_CLINICAL")
            state = engine.evaluate_runtime()
            is_operational = state.is_operational()
            report.results.append(ValidationResult(
                domain=ValidationDomain.PERFORMANCE,
                check_name="Offline execution readiness",
                status=ValidationStatus.PASSED if is_operational else ValidationStatus.FAILED,
                detail=f"OFFLINE_CLINICAL profile runtime state: {state.value} (operational={is_operational}).",
            ))
        except Exception as e:
            report.results.append(ValidationResult(
                domain=ValidationDomain.PERFORMANCE,
                check_name="Offline execution readiness",
                status=ValidationStatus.FAILED,
                detail=str(e),
            ))

        # Check 2: Resource-aware low-battery policy
        try:
            from src.edge import ResourceManager
            rm = ResourceManager()
            actions = rm.evaluate_resource_policies(battery_level=8.0, available_storage_mb=30.0)
            has_policies = len(actions) >= 2
            report.results.append(ValidationResult(
                domain=ValidationDomain.PERFORMANCE,
                check_name="Resource-aware low-battery policy",
                status=ValidationStatus.PASSED if has_policies else ValidationStatus.FAILED,
                detail=f"Policy count under stress: {len(actions)}.",
            ))
        except Exception as e:
            report.results.append(ValidationResult(
                domain=ValidationDomain.PERFORMANCE,
                check_name="Resource-aware low-battery policy",
                status=ValidationStatus.FAILED,
                detail=str(e),
            ))

        # Check 3: Deployment portability (all profiles loadable)
        try:
            from src.edge import DeploymentProfileManager
            profiles = DeploymentProfileManager.list_profiles()
            all_valid = all(DeploymentProfileManager.is_valid_profile(p) for p in profiles)
            report.results.append(ValidationResult(
                domain=ValidationDomain.PERFORMANCE,
                check_name="Deployment profile portability",
                status=ValidationStatus.PASSED if all_valid else ValidationStatus.FAILED,
                detail=f"Validated {len(profiles)} deployment profiles: {', '.join(profiles)}.",
            ))
        except Exception as e:
            report.results.append(ValidationResult(
                domain=ValidationDomain.PERFORMANCE,
                check_name="Deployment profile portability",
                status=ValidationStatus.FAILED,
                detail=str(e),
            ))

        report.summary = f"Performance validation: {report.passed_count}/{report.total_count} checks passed."
        return report
