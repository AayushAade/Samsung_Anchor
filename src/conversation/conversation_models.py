from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ConversationState(Enum):
    """
    Deterministic conversation states.
    """

    IDLE = "Idle"
    GREETING = "Greeting"
    LISTENING = "Listening"
    PATIENT_SPEAKING = "Patient Speaking"
    THINKING = "Thinking"
    RESPONDING = "Responding"
    WAITING = "Waiting"
    CONVERSATION_END = "Conversation End"
    SILENT_OBSERVATION = "Silent Observation"


class SpeakerRole(Enum):
    """
    Conversational turn roles.
    """

    PATIENT = "Patient"
    CAREGIVER = "Caregiver"
    DOCTOR = "Doctor"
    VISITOR = "Visitor"
    MEMORA = "Memora"


class ResponseStrategy(Enum):
    """
    Deterministic response strategies selected by ResponsePlanner.
    """

    GREETING = "Greeting"
    SUPPORTIVE_SILENCE = "Supportive Silence"
    QUESTION = "Question"
    CONFIRMATION = "Confirmation"
    ENCOURAGEMENT = "Encouragement"
    REMINDER = "Reminder"
    CONTEXT_RESTORATION = "Context Restoration"
    RELATIONSHIP_CUE = "Relationship Cue"
    SAFETY_ALERT = "Safety Alert"
    FAREWELL = "Farewell"


class InteractionType(Enum):
    """
    Deterministic interaction classifications.
    """

    GREETING = "Greeting"
    QUESTION = "Question"
    REMINDER = "Reminder"
    ORIENTATION = "Orientation"
    RELATIONSHIP = "Relationship"
    CASUAL = "Casual Conversation"
    CAREGIVER_REQUEST = "Caregiver Request"
    SAFETY = "Safety"
    UNKNOWN = "Unknown"


@dataclass
class ConversationContext:
    """
    Unified conversation snapshot consumed by ContextBuilder and Experience Platform.
    """

    state: ConversationState
    active_speaker: SpeakerRole
    response_strategy: ResponseStrategy
    interaction_type: InteractionType
    turn_count: int = 0
    elapsed_seconds: float = 0.0
    topic: str = "General Orientation & Support"
    owner: str = "Patient"
