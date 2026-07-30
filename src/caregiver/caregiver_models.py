"""
MEMORA Caregiver Intelligence & Clinical Oversight Data Models.

Defines immutable value objects, timeline event types, escalation levels, clinical summaries,
trend reports, and snapshot schemas.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TimelineEventType(str, Enum):
    """
    Classifies verified patient events recorded for clinical oversight.
    """

    CONTEXT_RESTORATION = "CONTEXT_RESTORATION"
    ROUTINE_COMPLETION = "ROUTINE_COMPLETION"
    OBJECT_ASSISTANCE = "OBJECT_ASSISTANCE"
    REASSURANCE = "REASSURANCE"
    DISORIENTATION = "DISORIENTATION"
    SAFETY_EVENT = "SAFETY_EVENT"
    CAREGIVER_INTERVENTION = "CAREGIVER_INTERVENTION"


class EscalationLevel(str, Enum):
    """
    Clinical escalation severity levels.
    """

    NONE = "NONE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    URGENT = "URGENT"

    def is_escalated(self) -> bool:
        """Return True if escalation level is above NONE."""
        return self != EscalationLevel.NONE

    def is_urgent_or_high(self) -> bool:
        """Return True if escalation level is HIGH or URGENT."""
        return self in (EscalationLevel.HIGH, EscalationLevel.URGENT)


@dataclass
class TimelineEvent:
    """
    Standardized, verifiable chronological event record.
    """

    event_type: TimelineEventType
    description: str
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def is_safety_related(self) -> bool:
        """Return True if event represents a safety concern or orientation issue."""
        return self.event_type in (TimelineEventType.SAFETY_EVENT, TimelineEventType.DISORIENTATION)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize TimelineEvent to a dictionary representation."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "description": self.description,
            "session_id": self.session_id,
            "metadata": dict(self.metadata),
            "timestamp": self.timestamp,
        }


@dataclass
class CaregiverSummary:
    """
    Structured summary of patient assistance activity and clinical status.
    """

    patient_id: str
    reporting_period: str
    completed_routines: List[str] = field(default_factory=list)
    assistance_events: int = 0
    confusion_events: int = 0
    object_assistance_events: int = 0
    escalation_level: EscalationLevel = EscalationLevel.NONE
    summary_id: str = field(default_factory=lambda: f"sum-{uuid.uuid4().hex[:8]}")
    generated_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def has_escalation(self) -> bool:
        """Return True if summary escalation level is above NONE."""
        return self.escalation_level != EscalationLevel.NONE

    def to_dict(self) -> Dict[str, Any]:
        """Serialize CaregiverSummary to a dictionary representation."""
        return {
            "summary_id": self.summary_id,
            "patient_id": self.patient_id,
            "reporting_period": self.reporting_period,
            "completed_routines": list(self.completed_routines),
            "assistance_events": self.assistance_events,
            "confusion_events": self.confusion_events,
            "object_assistance_events": self.object_assistance_events,
            "escalation_level": self.escalation_level.value,
            "generated_timestamp": self.generated_timestamp,
        }


@dataclass
class TrendReport:
    """
    Represents a deterministic longitudinal analysis of patient behavioral trends.
    """

    metric: str
    observation_window: str
    trend_direction: str  # "STABLE", "INCREASING", "DECREASING"
    supporting_evidence: List[str] = field(default_factory=list)
    confidence: float = 1.0
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def is_concerning(self) -> bool:
        """Return True if trend direction indicates increasing confusion or decreasing routine completion."""
        if self.metric in ("CONFUSION", "DISORIENTATION", "OBJECT") and self.trend_direction == "INCREASING":
            return True
        if self.metric == "ROUTINE" and self.trend_direction == "DECREASING":
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize TrendReport to a dictionary representation."""
        return {
            "metric": self.metric,
            "observation_window": self.observation_window,
            "trend_direction": self.trend_direction,
            "supporting_evidence": list(self.supporting_evidence),
            "confidence": self.confidence,
            "recommendations": list(self.recommendations),
            "timestamp": self.timestamp,
        }


@dataclass
class CaregiverSnapshot:
    """
    Point-in-time snapshot of caregiver events, summaries, and highest escalation level.
    """

    total_events_count: int
    summaries_generated_count: int
    highest_escalation: EscalationLevel
    checksum: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize CaregiverSnapshot to a dictionary representation."""
        return {
            "timestamp": self.timestamp,
            "total_events_count": self.total_events_count,
            "summaries_generated_count": self.summaries_generated_count,
            "highest_escalation": self.highest_escalation.value,
            "checksum": self.checksum,
        }
