"""
MEMORA Behaviour Intelligence Platform — Data Models.

Defines value objects and enumerations for:
- Observable Behaviour Models & Routine Patterns
- Transparent Predictions & Evidence-backed Uncertainty
- Longitudinal Cognitive Drift Metrics
- Personalisation Profiles & Caregiver Overrides
- Behaviour Timeline Entries & Caregiver Insights
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time
from typing import Any, Dict, List, Optional


# ======================================================================
# Behaviour & Routine Models
# ======================================================================

class ActivityCategory(str, Enum):
    MORNING_ROUTINE = "MORNING_ROUTINE"
    MEDICATION_ROUTINE = "MEDICATION_ROUTINE"
    READING_HABIT = "READING_HABIT"
    WALKING_HABIT = "WALKING_HABIT"
    MEAL_ROUTINE = "MEAL_ROUTINE"
    VISITOR_INTERACTION = "VISITOR_INTERACTION"
    OBJECT_PLACEMENT = "OBJECT_PLACEMENT"
    SLEEPING_ROUTINE = "SLEEPING_ROUTINE"
    GENERAL_ACTIVITY = "GENERAL_ACTIVITY"


@dataclass
class BehaviourModel:
    """Represents a recurring, observable activity pattern."""
    behaviour_id: str
    name: str
    category: ActivityCategory
    frequency_count: int = 1
    average_duration_mins: float = 15.0
    time_of_day_distribution: Dict[str, float] = field(default_factory=dict)  # "Morning": 0.7, "Evening": 0.3
    location: str = "Living Room"
    confidence: float = 0.50
    supporting_observations: List[str] = field(default_factory=list)
    last_observed_iso: str = field(default_factory=lambda: datetime.now().isoformat())
    trend_direction: str = "STABLE"  # STABLE, INCREASING, DECREASING

    def to_dict(self) -> Dict[str, Any]:
        return {
            "behaviour_id": self.behaviour_id,
            "name": self.name,
            "category": self.category.value,
            "frequency_count": self.frequency_count,
            "average_duration_mins": round(self.average_duration_mins, 1),
            "time_of_day_distribution": self.time_of_day_distribution,
            "location": self.location,
            "confidence": round(self.confidence, 3),
            "supporting_observations_count": len(self.supporting_observations),
            "last_observed": self.last_observed_iso,
            "trend_direction": self.trend_direction,
        }


@dataclass
class RoutinePattern:
    """Inferred daily or weekly routine pattern."""
    routine_id: str
    title: str
    category: ActivityCategory
    start_hour: int  # e.g., 8 for 8:00 AM
    end_hour: int    # e.g., 9 for 9:00 AM
    typical_location: str
    typical_object: Optional[str] = None
    confidence: float = 0.50
    observation_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "routine_id": self.routine_id,
            "title": self.title,
            "category": self.category.value,
            "time_window": f"{self.start_hour:02d}:00 - {self.end_hour:02d}:00",
            "typical_location": self.typical_location,
            "typical_object": self.typical_object,
            "confidence": round(self.confidence, 3),
            "observation_count": self.observation_count,
        }


# ======================================================================
# Predictive Assistance Models
# ======================================================================

class PredictionCategory(str, Enum):
    OBJECT_LOCATION = "OBJECT_LOCATION"
    NEXT_ACTIVITY = "NEXT_ACTIVITY"
    REMINDER_TIMING = "REMINDER_TIMING"
    CAREGIVER_CONTACT = "CAREGIVER_CONTACT"
    ROOM_TRANSITION = "ROOM_TRANSITION"


@dataclass
class PredictionResult:
    """Transparent prediction with explicit evidence and uncertainty."""
    category: PredictionCategory
    predicted_value: str
    confidence: float
    supporting_evidence: List[str]
    conflicting_evidence: List[str]
    uncertainty_score: float
    explanation: str
    generated_at_iso: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "predicted_value": self.predicted_value,
            "confidence": round(self.confidence, 3),
            "supporting_evidence": self.supporting_evidence,
            "conflicting_evidence": self.conflicting_evidence,
            "uncertainty_score": round(self.uncertainty_score, 3),
            "explanation": self.explanation,
            "generated_at": self.generated_at_iso,
        }


# ======================================================================
# Cognitive Drift Models (Longitudinal Trend Monitoring)
# ======================================================================

@dataclass
class DriftMetric:
    """Longitudinal observable metric for non-medical trend analysis."""
    metric_name: str  # e.g., "object_search_frequency", "repeated_questions_count"
    baseline_value: float
    current_value: float
    pct_change: float
    window_days: int = 30
    is_statistically_significant: bool = False
    evidence_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "baseline_value": round(self.baseline_value, 2),
            "current_value": round(self.current_value, 2),
            "pct_change": round(self.pct_change, 1),
            "window_days": self.window_days,
            "is_statistically_significant": self.is_statistically_significant,
            "evidence_summary": self.evidence_summary,
        }


# ======================================================================
# Personalisation & Timeline Models
# ======================================================================

@dataclass
class PersonalisationProfile:
    """Explainable user personalisation preferences with caregiver overrides."""
    patient_id: str = "P1"
    preferred_reminder_style: str = "Gentle Cue"  # Gentle Cue, Direct Instruction, Audible Chime
    preferred_verbosity: str = "CONCISE"          # CONCISE, DETAILED, MINIMAL
    frequently_contacted: List[str] = field(default_factory=lambda: ["Sarah (Daughter)", "Dr. Aris"])
    preferred_object_locations: Dict[str, str] = field(default_factory=lambda: {
        "reading glasses": "bedside table",
        "keys": "entryway hook",
        "wallet": "dresser drawer",
    })
    effective_care_strategies: List[str] = field(default_factory=lambda: ["Validation Therapy", "Gentle Orientation"])
    typical_schedule: Dict[str, str] = field(default_factory=lambda: {
        "Morning": "Breakfast & Morning Walk",
        "Afternoon": "Reading & Rest",
        "Evening": "Family Visit & Quiet Wind-down",
    })
    caregiver_overrides: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "preferred_reminder_style": self.preferred_reminder_style,
            "preferred_verbosity": self.preferred_verbosity,
            "frequently_contacted": self.frequently_contacted,
            "preferred_object_locations": self.preferred_object_locations,
            "effective_care_strategies": self.effective_care_strategies,
            "typical_schedule": self.typical_schedule,
            "caregiver_overrides": self.caregiver_overrides,
        }


@dataclass
class BehaviourTimelineEntry:
    """Single longitudinal activity event entry."""
    entry_id: str
    timestamp_iso: str
    activity_name: str
    location: str
    duration_mins: float
    stability_score: float
    supporting_evidence_ids: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp_iso,
            "activity_name": self.activity_name,
            "location": self.location,
            "duration_mins": round(self.duration_mins, 1),
            "stability_score": round(self.stability_score, 2),
            "evidence_count": len(self.supporting_evidence_ids),
        }


@dataclass
class CaregiverInsight:
    """Periodic evidence-backed caregiver summary report."""
    insight_id: str
    category: str  # Routine Consistency, Misplaced Objects, Reminder Effectiveness, Trend Alert
    title: str
    summary: str
    actionable_recommendation: str
    evidence_references: List[str]
    created_at_iso: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "category": self.category,
            "title": self.title,
            "summary": self.summary,
            "actionable_recommendation": self.actionable_recommendation,
            "evidence_references": self.evidence_references,
            "created_at": self.created_at_iso,
        }
