"""
MEMORA Alzheimer's Cognitive Assistance Data Models.

Defines immutable value objects, scenario classifications, assistance priorities,
execution plans, outcomes, and snapshot structures.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AssistanceScenario(str, Enum):
    """
    Classifies Alzheimer's cognitive assistance workflow categories.
    """

    CONTEXT_RESTORATION = "CONTEXT_RESTORATION"
    ROUTINE_GUIDANCE = "ROUTINE_GUIDANCE"
    OBJECT_RECALL = "OBJECT_RECALL"
    CAREGIVER_SUPPORT = "CAREGIVER_SUPPORT"
    REASSURANCE = "REASSURANCE"
    DISORIENTATION = "DISORIENTATION"
    REPEATED_QUESTION = "REPEATED_QUESTION"


class AssistancePriority(str, Enum):
    """
    Priority rating for cognitive assistance interventions.
    """

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class AssistancePlan:
    """
    Standardized, explainable execution plan for patient cognitive assistance.
    """

    session_id: str
    scenario: AssistanceScenario
    priority: AssistancePriority = AssistancePriority.NORMAL
    required_services: List[str] = field(default_factory=list)
    explanation_reference: str = ""
    plan_id: str = field(default_factory=lambda: f"plan-{uuid.uuid4().hex[:8]}")
    generated_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def is_high_priority(self) -> bool:
        """Return True if plan priority is HIGH or CRITICAL."""
        return self.priority in (AssistancePriority.HIGH, AssistancePriority.CRITICAL)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize AssistancePlan to a dictionary representation."""
        return {
            "plan_id": self.plan_id,
            "session_id": self.session_id,
            "scenario": self.scenario.value,
            "priority": self.priority.value,
            "required_services": list(self.required_services),
            "explanation_reference": self.explanation_reference,
            "generated_timestamp": self.generated_timestamp,
        }


@dataclass
class AssistanceOutcome:
    """
    Represents the result of executing an AssistancePlan.
    """

    success: bool
    actions_executed: List[str] = field(default_factory=list)
    escalation_required: bool = False
    caregiver_notification: Optional[str] = None
    confidence: float = 1.0
    summary: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize AssistanceOutcome to a dictionary representation."""
        return {
            "success": self.success,
            "actions_executed": list(self.actions_executed),
            "escalation_required": self.escalation_required,
            "caregiver_notification": self.caregiver_notification,
            "confidence": self.confidence,
            "summary": self.summary,
            "timestamp": self.timestamp,
        }


@dataclass
class AssistanceSnapshot:
    """
    Point-in-time snapshot of active assistance plans, outcomes, and checksum.
    """

    active_plans_count: int
    executed_outcomes_count: int
    escalations_count: int
    checksum: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize AssistanceSnapshot to a dictionary representation."""
        return {
            "timestamp": self.timestamp,
            "active_plans_count": self.active_plans_count,
            "executed_outcomes_count": self.executed_outcomes_count,
            "escalations_count": self.escalations_count,
            "checksum": self.checksum,
        }
