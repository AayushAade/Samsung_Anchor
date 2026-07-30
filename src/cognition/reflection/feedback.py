from enum import Enum
from pydantic import BaseModel
from typing import Optional

class FeedbackType(str, Enum):
    CORRECTION = "CORRECTION"
    CONFIRMATION = "CONFIRMATION"
    CONTRADICTION = "CONTRADICTION"
    IGNORED = "IGNORED" # E.g., user walked away while speaking

class FeedbackSource(str, Enum):
    VOICE = "VOICE"
    CAREGIVER_APP = "CAREGIVER_APP"
    SENSOR = "SENSOR"
    IMPLICIT = "IMPLICIT"

class FeedbackEvent(BaseModel):
    """
    A generic abstraction for feedback flowing into the Reflection Engine.
    """
    interaction_id: Optional[int]
    source: FeedbackSource
    feedback_type: FeedbackType
    content: Optional[str]
    timestamp: str
