from typing import Tuple
from src.conversation.conversation_models import ConversationState, ResponseStrategy, SpeakerRole
from src.interaction.events import PresenceEvent


class ConversationPolicy:
    """
    Deterministic conversation policy and transition rules.
    """

    def evaluate_policy(
        self,
        event: PresenceEvent,
        active_speaker: SpeakerRole,
        current_state: ConversationState,
        assistance_level: int = 0,
        attention_should_interrupt: bool = False,
    ) -> Tuple[ConversationState, ResponseStrategy]:
        """
        Evaluates turn transition rules deterministically.
        """
        # Rule 1: Safety Override (Level 5 Safety Intervention)
        if assistance_level >= 5 or "heart" in str(event).lower():
            return ConversationState.RESPONDING, ResponseStrategy.SAFETY_ALERT

        # Rule 2: Visitor / Person Arrived (Initial Greeting)
        if current_state in [ConversationState.IDLE, ConversationState.SILENT_OBSERVATION] and event.name:
            return ConversationState.GREETING, ResponseStrategy.GREETING

        # Rule 3: Patient Speaking (Listen quietly)
        if active_speaker == SpeakerRole.PATIENT and not attention_should_interrupt:
            return ConversationState.PATIENT_SPEAKING, ResponseStrategy.SUPPORTIVE_SILENCE

        # Rule 4: Caregiver or Doctor Speaking
        if active_speaker in [SpeakerRole.CAREGIVER, SpeakerRole.DOCTOR]:
            return ConversationState.RESPONDING, ResponseStrategy.CONFIRMATION

        # Rule 5: Executive Attention Triggered (Context Restoration / Cue)
        if attention_should_interrupt:
            if assistance_level == 2:
                return ConversationState.RESPONDING, ResponseStrategy.REMINDER
            return ConversationState.RESPONDING, ResponseStrategy.CONTEXT_RESTORATION

        # Default Rule: Silent Observation
        return ConversationState.SILENT_OBSERVATION, ResponseStrategy.SUPPORTIVE_SILENCE
