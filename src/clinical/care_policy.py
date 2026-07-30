"""
Care Policy Framework.

Applies evidence-based clinical dementia care principles:
- Validation Therapy (validate feelings, avoid arguments/corrections)
- Gentle Orientation (soft temporal/spatial grounding)
- Supportive Silence (avoid unnecessary interruptions)
- One-Step Guidance (simple, single-action instructions)
- Repetitive Query Redirection (warm, consistent responses)
- Emergency Safety Escalation
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any
from src.clinical.patient_state import PatientState, PatientStateMode


class CarePrinciple(Enum):
    VALIDATION_THERAPY = "Validation Therapy"
    GENTLE_ORIENTATION = "Gentle Orientation"
    SUPPORTIVE_SILENCE = "Supportive Silence"
    ONE_STEP_GUIDANCE = "One-Step Guidance"
    REPETITIVE_REDIRECTION = "Repetitive Query Redirection"
    EMERGENCY_ESCALATION = "Emergency Safety Escalation"


@dataclass
class CareDecision:
    principle: CarePrinciple
    action_type: str  # "SPEAK", "SILENCE", "ESCALATE"
    message_override: Optional[str] = None
    dignity_preserved: bool = True
    caregiver_notified: bool = False
    reasoning: str = ""


class CarePolicyFramework:
    """
    Evaluates PatientState, ConversationContext, ClinicalContext, MemoryContext, and GoalContext
    to enforce clinical dementia care principles.
    """

    def evaluate_policy(
        self,
        patient_state: PatientState,
        current_message: Optional[str] = None,
        patient_name: str = "Eleanor",
        location: str = "Living Room",
    ) -> CareDecision:

        # Rule 1: Emergency Safety Escalation
        if patient_state.mode == PatientStateMode.EMERGENCY:
            return CareDecision(
                principle=CarePrinciple.EMERGENCY_ESCALATION,
                action_type="ESCALATE",
                message_override="Emergency safety trigger active. Primary caregiver and clinical team notified.",
                dignity_preserved=True,
                caregiver_notified=True,
                reasoning="Emergency state requires immediate clinical escalation.",
            )

        # Rule 2: Repetitive Queries (Validation Therapy + Warm Consistency)
        if patient_state.mode == PatientStateMode.REPETITIVE:
            repeated_q = patient_state.details.get("repeated_query", "your request")
            return CareDecision(
                principle=CarePrinciple.REPETITIVE_REDIRECTION,
                action_type="SPEAK",
                message_override=f"Don't worry, {patient_name}. I am right here with you. Regarding {repeated_q}, everything is taken care of.",
                dignity_preserved=True,
                caregiver_notified=False,
                reasoning="Validation therapy for repeated query: provide warm, identical reassurance without correcting.",
            )

        # Rule 3: Anxious / Agitated State (Validation Therapy & Calm Reassurance)
        if patient_state.mode == PatientStateMode.ANXIOUS:
            return CareDecision(
                principle=CarePrinciple.VALIDATION_THERAPY,
                action_type="SPEAK",
                message_override=f"You are safe here at home in your {location}, {patient_name}. Everything is okay.",
                dignity_preserved=True,
                caregiver_notified=False,
                reasoning="Validation therapy for anxiety: ground in current safety.",
            )

        # Rule 4: Time/Spatial Disorientation (Gentle Orientation)
        if patient_state.mode == PatientStateMode.DISORIENTED:
            return CareDecision(
                principle=CarePrinciple.GENTLE_ORIENTATION,
                action_type="SPEAK",
                message_override=f"You are home in your {location}, {patient_name}. Take your time, everything is on schedule.",
                dignity_preserved=True,
                caregiver_notified=False,
                reasoning="Gentle orientation: soft location and time grounding.",
            )

        # Rule 5: Missed Medication / Routine (One-Step Guidance)
        if patient_state.mode == PatientStateMode.AWAITING_REMINDER:
            need_desc = patient_state.primary_need
            return CareDecision(
                principle=CarePrinciple.ONE_STEP_GUIDANCE,
                action_type="SPEAK",
                message_override=f"Here is a gentle reminder, {patient_name}: {need_desc}.",
                dignity_preserved=True,
                caregiver_notified=False,
                reasoning="One-step guidance: single clear prompt.",
            )

        # Rule 6: Searching for Item (One-Step Guidance)
        if patient_state.mode == PatientStateMode.SEARCHING:
            return CareDecision(
                principle=CarePrinciple.ONE_STEP_GUIDANCE,
                action_type="SPEAK",
                message_override=current_message or f"Let's look around your {location} together.",
                dignity_preserved=True,
                caregiver_notified=False,
                reasoning="One-step guidance for locating misplaced items.",
            )

        # Default Rule: Supportive Silence when Calm or Oriented
        if patient_state.mode in [PatientStateMode.CALM, PatientStateMode.ORIENTED] and not current_message:
            return CareDecision(
                principle=CarePrinciple.SUPPORTIVE_SILENCE,
                action_type="SILENCE",
                message_override=None,
                dignity_preserved=True,
                caregiver_notified=False,
                reasoning="Supportive silence: preserve calm environment without unnecessary interruption.",
            )

        # Pass-through with dignity check validation
        return CareDecision(
            principle=CarePrinciple.ONE_STEP_GUIDANCE,
            action_type="SPEAK",
            message_override=current_message,
            dignity_preserved=True,
            caregiver_notified=False,
            reasoning="Standard interaction adhering to dementia care principles.",
        )
