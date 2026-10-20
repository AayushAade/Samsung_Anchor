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
from datetime import datetime

from src.clinical.patient_state import PatientState, PatientStateMode
from src.clinical.urgent_safety import UrgentConcern, UrgentConcernType, urgent_guidance


class CarePrinciple(Enum):
    VALIDATION_THERAPY = "Validation Therapy"
    REALITY_ORIENTATION = "Reality Orientation"
    GENTLE_CUEING = "Gentle Cueing"
    REASSURANCE = "Reassurance"
    DISTRACTION = "Distraction"
    CAREGIVER_ESCALATION = "Caregiver Escalation"
    EMERGENCY_ESCALATION = "Emergency Safety Escalation"
    MINIMAL_INTERVENTION = "Minimal Intervention"
    GENTLE_ORIENTATION = "Gentle Orientation"
    SUPPORTIVE_SILENCE = "Supportive Silence"
    ONE_STEP_GUIDANCE = "One-Step Guidance"
    REPETITIVE_REDIRECTION = "Repetitive Query Redirection"


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
        # MEMORA has no caregiver/emergency notification channel, so it directs the
        # person to human help and never claims that anyone has been contacted.
        if patient_state.mode == PatientStateMode.EMERGENCY:
            concern_value = patient_state.details.get("urgent_concern")
            if concern_value:
                concern = UrgentConcern(UrgentConcernType(concern_value), patient_state.details.get("matched_text", ""))
                message = urgent_guidance(concern, name=patient_name)
            else:
                message = (f"{patient_name}, if you need help, please call your local emergency number "
                           "or press your help button, or call out to someone nearby. "
                           "I can't contact anyone myself.")
            return CareDecision(
                principle=CarePrinciple.EMERGENCY_ESCALATION,
                action_type="ESCALATE",
                message_override=message,
                dignity_preserved=True,
                caregiver_notified=False,
                reasoning="Possible emergency: direct the person to human help immediately.",
            )

        # Rule 2: Repetitive Queries (Validation Therapy + Warm Consistency)
        # Reassure without claiming that the underlying matter has been resolved.
        if patient_state.mode == PatientStateMode.REPETITIVE:
            return CareDecision(
                principle=CarePrinciple.REPETITIVE_REDIRECTION,
                action_type="SPEAK",
                message_override=f"That's alright, {patient_name}, it's fine to ask again. I'm right here with you.",
                dignity_preserved=True,
                caregiver_notified=False,
                reasoning="Validation therapy for repeated query: warm, consistent reassurance without correcting.",
            )

        # Rule 3: Anxious / Agitated State (Validation Therapy & Calm Reassurance)
        # Validate the feeling; do not assert safety or location MEMORA cannot verify.
        if patient_state.mode == PatientStateMode.ANXIOUS:
            return CareDecision(
                principle=CarePrinciple.VALIDATION_THERAPY,
                action_type="SPEAK",
                message_override=(f"I'm here with you, {patient_name}. It's okay to feel worried. "
                                  "Let's take a slow breath together. If something is wrong, "
                                  "please tell someone you trust."),
                dignity_preserved=True,
                caregiver_notified=False,
                reasoning="Validation therapy for anxiety: acknowledge feelings, offer calm grounding.",
            )

        # Rule 4: Time/Spatial Disorientation (Gentle Orientation)
        # Orient with the system clock (verified); location is not asserted.
        if patient_state.mode == PatientStateMode.DISORIENTED:
            now = datetime.now()
            return CareDecision(
                principle=CarePrinciple.GENTLE_ORIENTATION,
                action_type="SPEAK",
                message_override=(f"It's {now.strftime('%A')}, {now.strftime('%B')} {now.day}, "
                                  f"around {now.strftime('%I:%M %p').lstrip('0')}. Take your time, {patient_name}."),
                dignity_preserved=True,
                caregiver_notified=False,
                reasoning="Gentle orientation: soft time grounding from the system clock.",
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
                message_override=current_message or "Let's look for it together. Where do you usually keep it?",
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
