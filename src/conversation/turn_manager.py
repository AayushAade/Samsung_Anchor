from typing import Optional
from src.conversation.conversation_models import SpeakerRole
from src.interaction.events import PresenceEvent


class TurnManager:
    """
    Manages conversational turn taking and active speaker tracking.
    """

    def __init__(self) -> None:
        self.active_speaker: SpeakerRole = SpeakerRole.PATIENT

    def set_speaker(self, role: SpeakerRole) -> None:
        self.active_speaker = role

    def get_active_speaker(self) -> SpeakerRole:
        return self.active_speaker

    def determine_speaker_from_event(self, event: PresenceEvent) -> SpeakerRole:
        """
        Infers the active speaker role from presence event metadata.
        """
        rel = (event.relationship or "").lower()
        if "doctor" in rel:
            self.active_speaker = SpeakerRole.DOCTOR
        elif "caregiver" in rel or "nurse" in rel:
            self.active_speaker = SpeakerRole.CAREGIVER
        elif event.name and event.name.lower() != "patient":
            self.active_speaker = SpeakerRole.VISITOR
        else:
            self.active_speaker = SpeakerRole.PATIENT
        return self.active_speaker
