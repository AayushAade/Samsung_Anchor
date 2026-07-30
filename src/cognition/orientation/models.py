from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class RoutineStage(Enum):
    MORNING = "Morning"
    BREAKFAST = "Breakfast Routine"
    MEDICATION = "Medication Time"
    LUNCH = "Lunch Preparation"
    AFTERNOON = "Afternoon Activity"
    FAMILY_VISIT = "Family Visit"
    EVENING = "Evening Relaxation"
    NIGHT = "Night Routine"


@dataclass
class DailyOrientationContext:
    """
    Represents the daily orientation anchors and life continuity context for the patient.
    """
    routine_stage: str
    current_day: str
    approximate_time: str
    today_events: List[str] = field(default_factory=list)
    recent_activity: Optional[str] = None
    upcoming_activity: Optional[str] = None
    confidence: float = 0.9
