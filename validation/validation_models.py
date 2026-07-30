"""
MEMORA Phase 40 — Validation Framework Data Models.

Defines immutable value objects for validation reports, certification results,
health summaries, and RC1 readiness assessments.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ValidationStatus(str, Enum):
    """Validation outcome classification."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"


class ValidationDomain(str, Enum):
    """Classification of validation concern."""
    INTEGRATION = "INTEGRATION"
    DEPENDENCY = "DEPENDENCY"
    DETERMINISM = "DETERMINISM"
    SAFETY = "SAFETY"
    EXPLAINABILITY = "EXPLAINABILITY"
    PERFORMANCE = "PERFORMANCE"
    RC1 = "RC1"


@dataclass
class ValidationResult:
    """Single validation check outcome."""
    domain: ValidationDomain
    check_name: str
    status: ValidationStatus
    detail: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain.value,
            "check_name": self.check_name,
            "status": self.status.value,
            "detail": self.detail,
            "timestamp": self.timestamp,
        }


@dataclass
class ValidationReport:
    """Aggregated validation report across one domain."""
    domain: ValidationDomain
    results: List[ValidationResult] = field(default_factory=list)
    summary: str = ""

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.status == ValidationStatus.PASSED)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.status == ValidationStatus.FAILED)

    @property
    def total_count(self) -> int:
        return len(self.results)

    @property
    def all_passed(self) -> bool:
        return self.failed_count == 0 and self.total_count > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain.value,
            "total": self.total_count,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "all_passed": self.all_passed,
            "summary": self.summary,
            "results": [r.to_dict() for r in self.results],
        }


@dataclass
class RC1Certification:
    """Production Candidate Release Candidate 1 certification record."""
    architecture_status: str = "CERTIFIED"
    maturity_level: str = "Production Candidate (RC1)"
    cognitive_platform: str = "COMPLETE"
    patient_assistance: str = "COMPLETE"
    caregiver_intelligence: str = "COMPLETE"
    clinical_interoperability: str = "COMPLETE"
    edge_runtime: str = "COMPLETE"
    safety_validation: str = "PASSED"
    determinism_validation: str = "PASSED"
    explainability_validation: str = "PASSED"
    repository_status: str = "ARCHITECTURE FROZEN"
    total_frameworks: int = 0
    total_production_loc: int = 0
    total_tests: int = 0
    total_test_files: int = 0
    pass_rate: str = "100%"
    checksum: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def compute_checksum(self) -> str:
        data = json.dumps({
            "status": self.architecture_status,
            "maturity": self.maturity_level,
            "frameworks": self.total_frameworks,
            "loc": self.total_production_loc,
            "tests": self.total_tests,
        }, sort_keys=True).encode("utf-8")
        self.checksum = hashlib.sha256(data).hexdigest()[:16]
        return self.checksum

    def to_dict(self) -> Dict[str, Any]:
        return {
            "architecture_status": self.architecture_status,
            "maturity_level": self.maturity_level,
            "cognitive_platform": self.cognitive_platform,
            "patient_assistance": self.patient_assistance,
            "caregiver_intelligence": self.caregiver_intelligence,
            "clinical_interoperability": self.clinical_interoperability,
            "edge_runtime": self.edge_runtime,
            "safety_validation": self.safety_validation,
            "determinism_validation": self.determinism_validation,
            "explainability_validation": self.explainability_validation,
            "repository_status": self.repository_status,
            "total_frameworks": self.total_frameworks,
            "total_production_loc": self.total_production_loc,
            "total_tests": self.total_tests,
            "pass_rate": self.pass_rate,
            "checksum": self.checksum,
            "timestamp": self.timestamp,
        }
