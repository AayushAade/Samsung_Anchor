"""
MEMORA Central Cognitive Integrity Engine.

Public façade coordinating IntegrityValidator and ConsistencyChecker to generate
unified, read-only IntegrityReport objects without modifying system state.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.integrity.consistency_checker import ConsistencyChecker
from src.integrity.integrity_models import IntegrityIssue, IntegrityLevel, IntegrityReport
from src.integrity.integrity_validator import IntegrityValidator


class IntegrityEngine:
    """
    Read-only public façade for ecosystem integrity and consistency diagnostics.
    """

    def __init__(
        self,
        validator: Optional[Any] = None,
        consistency_checker: Optional[Any] = None,
    ) -> None:
        self.validator = validator if isinstance(validator, IntegrityValidator) else IntegrityValidator()
        self.consistency_checker = (
            consistency_checker if isinstance(consistency_checker, ConsistencyChecker) else ConsistencyChecker()
        )

    def run_integrity_check(
        self,
        pipeline: Optional[Any] = None,
        service_registry: Optional[Any] = None,
        knowledge_engine: Optional[Any] = None,
        memory_engine: Optional[Any] = None,
        executive_engine: Optional[Any] = None,
        experience_engine: Optional[Any] = None,
        session_manager: Optional[Any] = None,
        reasoning_engine: Optional[Any] = None,
        pipeline_stage_order: Optional[List[str]] = None,
    ) -> IntegrityReport:
        """
        Execute read-only ecosystem validation and cross-subsystem consistency checks.
        Returns a comprehensive IntegrityReport.
        """
        start_time = time.time()
        issues: List[IntegrityIssue] = []

        # 1. Structural & Interface Validation Checks
        v_issues = self.validator.validate_subsystems(
            pipeline=pipeline,
            service_registry=service_registry,
        )
        issues.extend(v_issues)

        # 2. Cross-Subsystem Reference & Order Consistency Checks
        c_issues = self.consistency_checker.check_consistency(
            knowledge_engine=knowledge_engine or (getattr(pipeline, "knowledge_engine", None) if pipeline else None),
            memory_engine=memory_engine or (getattr(pipeline, "memory_engine", None) if pipeline else None),
            executive_engine=executive_engine or (getattr(pipeline, "executive_engine", None) if pipeline else None),
            experience_engine=experience_engine or (getattr(pipeline, "experience_engine", None) if pipeline else None),
            session_manager=session_manager,
            reasoning_engine=reasoning_engine or (getattr(pipeline, "reasoning_engine", None) if pipeline else None),
            pipeline_stage_order=pipeline_stage_order,
        )
        issues.extend(c_issues)

        # 3. Calculate Check Statistics & Overall Status
        total_checks = 15  # Fixed baseline of core structural & reference checks performed
        failed_checks = len(issues)
        passed_checks = max(0, total_checks - failed_checks)
        warning_count = sum(1 for i in issues if i.severity in (IntegrityLevel.WARNING, IntegrityLevel.INFO))
        critical_count = sum(1 for i in issues if i.severity in (IntegrityLevel.ERROR, IntegrityLevel.CRITICAL))

        overall_status = "HEALTHY"
        if critical_count > 0:
            overall_status = "CRITICAL_ISSUES_DETECTED"
        elif warning_count > 0:
            overall_status = "WARNINGS_DETECTED"

        return IntegrityReport(
            validation_time=datetime.now().isoformat(),
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warning_count=warning_count,
            issues=issues,
            overall_status=overall_status,
        )
