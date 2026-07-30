"""
MEMORA Cognitive Integrity & Consistency Framework Data Models.

Defines immutable value objects and enums for ecosystem integrity reporting.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class IntegrityLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class IntegrityCategory(str, Enum):
    KNOWLEDGE = "KNOWLEDGE"
    MEMORY = "MEMORY"
    EXPERIENCE = "EXPERIENCE"
    REASONING = "REASONING"
    EXECUTIVE = "EXECUTIVE"
    TRUST = "TRUST"
    SESSION = "SESSION"
    RUNTIME = "RUNTIME"
    PIPELINE = "PIPELINE"


@dataclass
class IntegrityIssue:
    """
    Represents a single integrity anomaly or inconsistency detected in the ecosystem.
    """

    category: IntegrityCategory
    severity: IntegrityLevel
    subsystem: str
    description: str
    affected_reference: str = ""
    recommendation: str = ""
    issue_id: str = field(default_factory=lambda: f"iss-{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "timestamp": self.timestamp,
            "category": self.category.value,
            "severity": self.severity.value,
            "subsystem": self.subsystem,
            "description": self.description,
            "affected_reference": self.affected_reference,
            "recommendation": self.recommendation,
        }


@dataclass
class IntegrityReport:
    """
    Unified ecosystem integrity diagnostic report.
    """

    validation_time: str = field(default_factory=lambda: datetime.now().isoformat())
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    warning_count: int = 0
    issues: List[IntegrityIssue] = field(default_factory=list)
    overall_status: str = "HEALTHY"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "validation_time": self.validation_time,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "warning_count": self.warning_count,
            "issues": [issue.to_dict() for issue in self.issues],
            "overall_status": self.overall_status,
        }
