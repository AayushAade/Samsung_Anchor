"""
MEMORA Experience Learning Data Models.

Provides unified value objects for:
- Append-only Execution Records and Outcomes
- Reusable Execution Patterns
- Failure Analysis & Root Cause Records
- Calibrated Confidence Recommendations
- Caregiver Preferences
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ExecutionOutcome(str, Enum):
    SUCCESSFUL = "SUCCESSFUL"
    PARTIALLY_SUCCESSFUL = "PARTIALLY_SUCCESSFUL"
    RECOVERED = "RECOVERED"
    INTERRUPTED = "INTERRUPTED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    UNKNOWN = "UNKNOWN"


@dataclass
class ExecutionRecord:
    """
    Append-only record of a completed executive plan execution.
    """

    goal_id: str
    plan_id: str
    tasks_executed: List[Dict[str, Any]]
    completion_status: ExecutionOutcome = ExecutionOutcome.SUCCESSFUL
    interruptions: List[Dict[str, Any]] = field(default_factory=list)
    recovery_actions: List[Dict[str, Any]] = field(default_factory=list)
    confidence_evolution: List[float] = field(default_factory=list)
    latency_ms: float = 0.0
    environment_context: Dict[str, Any] = field(default_factory=dict)
    caregiver_involvement: bool = False
    execution_id: str = field(default_factory=lambda: f"exc-{uuid.uuid4().hex[:8]}")
    timestamp_iso: str = field(default_factory=lambda: datetime.now().isoformat())
    created_ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "goal_id": self.goal_id,
            "plan_id": self.plan_id,
            "tasks_executed_count": len(self.tasks_executed),
            "completion_status": self.completion_status.value,
            "interruptions_count": len(self.interruptions),
            "recovery_actions_count": len(self.recovery_actions),
            "confidence_evolution": [round(c, 3) for c in self.confidence_evolution],
            "latency_ms": round(self.latency_ms, 3),
            "environment_context": self.environment_context,
            "caregiver_involvement": self.caregiver_involvement,
            "timestamp_iso": self.timestamp_iso,
        }


@dataclass
class ExecutionPattern:
    """
    Reusable execution pattern derived from accumulated historical statistics.
    """

    goal_title: str
    task_sequence_titles: List[str]
    pattern_id: str = field(default_factory=lambda: f"pat-{uuid.uuid4().hex[:8]}")
    usage_count: int = 1
    success_count: int = 1
    success_rate: float = 1.0
    average_latency_ms: float = 0.0
    average_confidence: float = 0.80
    failure_causes: List[str] = field(default_factory=list)
    last_successful_iso: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "goal_title": self.goal_title,
            "task_sequence": list(self.task_sequence_titles),
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "success_rate": round(self.success_rate, 3),
            "average_latency_ms": round(self.average_latency_ms, 3),
            "average_confidence": round(self.average_confidence, 3),
            "failure_causes": list(self.failure_causes),
            "last_successful_iso": self.last_successful_iso,
        }


@dataclass
class FailureAnalysisRecord:
    """
    Structured failure breakdown for an unsuccessful plan execution.
    """

    execution_id: str
    root_cause: str
    missing_evidence: List[str] = field(default_factory=list)
    incorrect_assumptions: List[str] = field(default_factory=list)
    sensor_limitations: List[str] = field(default_factory=list)
    interruption_causes: List[str] = field(default_factory=list)
    planning_weaknesses: List[str] = field(default_factory=list)
    recovery_effectiveness: str = "NOT_APPLICABLE"
    explanation: str = ""
    failure_id: str = field(default_factory=lambda: f"flr-{uuid.uuid4().hex[:8]}")
    timestamp_iso: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "execution_id": self.execution_id,
            "root_cause": self.root_cause,
            "missing_evidence": list(self.missing_evidence),
            "incorrect_assumptions": list(self.incorrect_assumptions),
            "sensor_limitations": list(self.sensor_limitations),
            "interruption_causes": list(self.interruption_causes),
            "planning_weaknesses": list(self.planning_weaknesses),
            "recovery_effectiveness": self.recovery_effectiveness,
            "explanation": self.explanation,
            "timestamp_iso": self.timestamp_iso,
        }


@dataclass
class CalibratedConfidence:
    """
    Calibrated confidence recommendation for executive planning.
    """

    predicted_confidence: float
    historical_success_rate: float
    execution_variance: float
    recommended_confidence: float
    calibration_explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "predicted_confidence": round(self.predicted_confidence, 3),
            "historical_success_rate": round(self.historical_success_rate, 3),
            "execution_variance": round(self.execution_variance, 3),
            "recommended_confidence": round(self.recommended_confidence, 3),
            "calibration_explanation": self.calibration_explanation,
        }


@dataclass
class CaregiverPreference:
    """
    Explicit, editable caregiver operational preference.
    """

    preference_key: str
    preference_value: Any
    category: str = "GENERAL"
    description: str = ""
    last_updated_iso: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "preference_key": self.preference_key,
            "preference_value": self.preference_value,
            "category": self.category,
            "description": self.description,
            "last_updated_iso": self.last_updated_iso,
        }
