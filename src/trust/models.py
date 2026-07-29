"""
MEMORA Trust, Safety, Reliability & Real-World Deployment Framework — Data Models.

Defines value objects and enumerations for:
- Safety Manager & Guardrails
- Uncertainty & Evidence Accumulation
- Audit & Traceability
- Caregiver Preferences
- Privacy & Data Retention Lifecycle
- Degradation & Failure Recovery
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time
from typing import Any, Dict, List, Optional

from src.cognition.cos.models import CognitiveAction, CognitiveActionType


# ======================================================================
# Safety Guardrails Models
# ======================================================================

class SafetyStatus(str, Enum):
    APPROVED = "APPROVED"
    MODIFIED = "MODIFIED"
    DOWNGRADED = "DOWNGRADED"
    BLOCKED = "BLOCKED"
    ESCALATED = "ESCALATED"


@dataclass
class SafetyCheckResult:
    """Result of an individual safety check rule."""
    check_name: str
    passed: bool
    reason: str
    severity: str = "INFO"  # INFO, WARNING, CRITICAL
    action_override: Optional[CognitiveAction] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_name": self.check_name,
            "passed": self.passed,
            "reason": self.reason,
            "severity": self.severity,
            "has_override": self.action_override is not None,
        }


@dataclass
class SafetyEvaluation:
    """Aggregated evaluation of all safety checks for a proposed CognitiveAction."""
    status: SafetyStatus
    original_action: CognitiveAction
    final_action: CognitiveAction
    check_results: List[SafetyCheckResult] = field(default_factory=list)
    evaluation_reason: str = "All safety checks passed."
    evaluated_at_iso: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "original_action_type": self.original_action.action_type.value,
            "final_action_type": self.final_action.action_type.value,
            "check_count": len(self.check_results),
            "passed_count": sum(1 for c in self.check_results if c.passed),
            "failed_checks": [c.check_name for c in self.check_results if not c.passed],
            "evaluation_reason": self.evaluation_reason,
            "evaluated_at": self.evaluated_at_iso,
        }


# ======================================================================
# Evidence & Uncertainty Models
# ======================================================================

class EvidenceType(str, Enum):
    FACE_OBSERVATION = "FACE_OBSERVATION"
    OBJECT_SIGHTING = "OBJECT_SIGHTING"
    SPEECH_TRANSCRIPT = "SPEECH_TRANSCRIPT"
    TEMPORAL_SIGNAL = "TEMPORAL_SIGNAL"
    GOAL_SIGNAL = "GOAL_SIGNAL"
    CONTEXT_SIGNAL = "CONTEXT_SIGNAL"


@dataclass
class EvidenceRecord:
    """Atomic piece of evidence collected over time."""
    evidence_id: str
    evidence_type: EvidenceType
    source: str
    key: str
    value: str
    weight: float
    confidence: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type.value,
            "source": self.source,
            "key": self.key,
            "value": self.value,
            "weight": round(self.weight, 3),
            "confidence": round(self.confidence, 3),
            "age_seconds": round(time.time() - self.timestamp, 1),
        }


@dataclass
class EvidencePoolSummary:
    """Summary snapshot of accumulated evidence for an entity."""
    entity_key: str
    supporting_count: int
    contradicting_count: int
    accumulated_confidence: float
    net_weight: float
    is_conflicted: bool
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_key": self.entity_key,
            "supporting_count": self.supporting_count,
            "contradicting_count": self.contradicting_count,
            "accumulated_confidence": round(self.accumulated_confidence, 3),
            "net_weight": round(self.net_weight, 3),
            "is_conflicted": self.is_conflicted,
            "explanation": self.explanation,
        }


# ======================================================================
# Audit & Traceability Models
# ======================================================================

class AuditExportFormat(str, Enum):
    JSON = "JSON"
    CSV = "CSV"
    REDACTED_JSON = "REDACTED_JSON"


@dataclass
class TrustAuditRecord:
    """Comprehensive, privacy-conscious audit record for a cognitive cycle."""
    audit_id: str
    timestamp_iso: str
    cycle_id: int
    triggering_event: str
    active_goal: Optional[str]
    active_context_summary: str
    working_memory_keys: List[str]
    selected_care_policy: str
    evidence_summary: str
    safety_status: str
    safety_checks_passed: int
    safety_checks_failed: List[str]
    proposed_action: str
    final_action: str
    explanation: str
    pii_redacted: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "timestamp": self.timestamp_iso,
            "cycle_id": self.cycle_id,
            "triggering_event": self.triggering_event,
            "active_goal": self.active_goal,
            "active_context_summary": self.active_context_summary,
            "working_memory_keys": self.working_memory_keys,
            "selected_care_policy": self.selected_care_policy,
            "evidence_summary": self.evidence_summary,
            "safety_status": self.safety_status,
            "safety_checks_passed": self.safety_checks_passed,
            "safety_checks_failed": self.safety_checks_failed,
            "proposed_action": self.proposed_action,
            "final_action": self.final_action,
            "explanation": self.explanation,
            "pii_redacted": self.pii_redacted,
        }


# ======================================================================
# Privacy & Retention Models
# ======================================================================

class DataCategory(str, Enum):
    TRANSIENT_WORKING_MEMORY = "TRANSIENT_WORKING_MEMORY"
    OPERATIONAL_LOGS = "OPERATIONAL_LOGS"
    AUDIT_RECORDS = "AUDIT_RECORDS"
    CAREGIVER_REPORTS = "CAREGIVER_REPORTS"
    LONG_TERM_MEMORY = "LONG_TERM_MEMORY"


@dataclass
class RetentionPolicy:
    """Configurable retention rule for a specific data category."""
    category: DataCategory
    retention_period_seconds: float
    auto_purge_enabled: bool = True
    encrypt_at_rest: bool = True
    pii_redaction_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "retention_period_days": round(self.retention_period_seconds / 86400.0, 1),
            "auto_purge_enabled": self.auto_purge_enabled,
            "encrypt_at_rest": self.encrypt_at_rest,
            "pii_redaction_required": self.pii_redaction_required,
        }


# ======================================================================
# Failure Recovery & Graceful Degradation Models
# ======================================================================

class SubsystemHealthState(str, Enum):
    FULL = "FULL"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class DegradationStatus:
    """Status report of runtime degradation and active fallback modes."""
    camera_state: SubsystemHealthState = SubsystemHealthState.FULL
    microphone_state: SubsystemHealthState = SubsystemHealthState.FULL
    face_recognition_state: SubsystemHealthState = SubsystemHealthState.FULL
    object_detection_state: SubsystemHealthState = SubsystemHealthState.FULL
    speech_synthesis_state: SubsystemHealthState = SubsystemHealthState.FULL
    active_fallbacks: List[str] = field(default_factory=list)
    overall_health: str = "HEALTHY"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "camera_state": self.camera_state.value,
            "microphone_state": self.microphone_state.value,
            "face_recognition_state": self.face_recognition_state.value,
            "object_detection_state": self.object_detection_state.value,
            "speech_synthesis_state": self.speech_synthesis_state.value,
            "active_fallbacks": self.active_fallbacks,
            "overall_health": self.overall_health,
        }
