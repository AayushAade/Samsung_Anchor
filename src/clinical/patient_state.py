"""
Patient State Model.

Dynamically evaluates patient cognitive/emotional state observations (Calm, Searching, Confused, Repetitive,
Oriented, Disoriented, Anxious, Awaiting Reminder, Emergency) without mutating existing data models.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any, Dict


class PatientStateMode(Enum):
    CALM = "Calm"
    SEARCHING = "Searching for Item"
    CONFUSED = "Confused"
    REPETITIVE = "Repetitive Queries"
    ORIENTED = "Oriented"
    DISORIENTED = "Time/Spatial Disorientation"
    ANXIOUS = "Anxious / Agitated"
    AWAITING_REMINDER = "Awaiting Scheduled Medication/Routine"
    EMERGENCY = "Emergency Safety Trigger"


@dataclass
class PatientState:
    mode: PatientStateMode
    confidence: float
    primary_need: str
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    details: Dict[str, Any] = field(default_factory=dict)


class PatientStateEvaluator:
    """
    Evaluates patient observations from multi-domain context (CognitiveContext, PresenceEvent,
    Speech Transcript, Clinical Ecosystem) without hardcoded assumptions.
    """

    def __init__(self) -> None:
        self._query_history: list[str] = []

    def evaluate(
        self,
        cognitive_context: Optional[Any] = None,
        presence_event: Optional[Any] = None,
        user_speech: Optional[str] = None,
        emergency_active: bool = False,
        missed_medications: Optional[list] = None,
    ) -> PatientState:
        now_iso = datetime.now().isoformat()

        # 1. Emergency Override
        if emergency_active:
            return PatientState(
                mode=PatientStateMode.EMERGENCY,
                confidence=1.0,
                primary_need="Immediate safety escalation and caregiver notification",
                last_updated=now_iso,
            )

        # 2. Missed Medication Priority
        if missed_medications and len(missed_medications) > 0:
            med_names = ", ".join(missed_medications)
            return PatientState(
                mode=PatientStateMode.AWAITING_REMINDER,
                confidence=0.95,
                primary_need=f"Gentle reminder for missed medication: {med_names}",
                last_updated=now_iso,
            )

        # 3. Speech Transcript Analysis
        if user_speech:
            speech_clean = user_speech.lower().strip()
            self._query_history.append(speech_clean)
            if len(self._query_history) > 10:
                self._query_history.pop(0)

            # Check for repetitive query loop (e.g. asking same/similar question multiple times)
            if self._query_history.count(speech_clean) >= 2:
                return PatientState(
                    mode=PatientStateMode.REPETITIVE,
                    confidence=0.90,
                    primary_need="Validation Therapy and calm, consistent reassurance",
                    last_updated=now_iso,
                    details={"repeated_query": user_speech},
                )

            # Searching keywords
            if any(w in speech_clean for w in ["where is", "where are", "lost", "find my", "cannot find", "can't find"]):
                return PatientState(
                    mode=PatientStateMode.SEARCHING,
                    confidence=0.88,
                    primary_need="Locate missing personal item",
                    last_updated=now_iso,
                )

            # Disorientation keywords
            if any(w in speech_clean for w in ["what time", "what day", "where am i", "what month", "who are you"]):
                return PatientState(
                    mode=PatientStateMode.DISORIENTED,
                    confidence=0.85,
                    primary_need="Gentle temporal and spatial orientation",
                    last_updated=now_iso,
                )

            # Anxiety keywords
            if any(w in speech_clean for w in ["scared", "worried", "anxious", "help me", "frightened"]):
                return PatientState(
                    mode=PatientStateMode.ANXIOUS,
                    confidence=0.92,
                    primary_need="Emotional reassurance and grounding in present safety",
                    last_updated=now_iso,
                )

        # 4. Cognitive Context Evaluation
        if cognitive_context and getattr(cognitive_context, "temporal", None):
            time_str = str(getattr(cognitive_context.temporal, "time_of_day", "Day"))
            return PatientState(
                mode=PatientStateMode.ORIENTED,
                confidence=0.80,
                primary_need=f"Normal routine during {time_str}",
                last_updated=now_iso,
            )

        return PatientState(
            mode=PatientStateMode.CALM,
            confidence=0.95,
            primary_need="Supportive silence and ambient monitoring",
            last_updated=now_iso,
        )

    def reset(self) -> None:
        self._query_history.clear()
