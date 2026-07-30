from src.conversation.conversation_models import SpeakerRole
from src.conversation.turn_manager import TurnManager
from src.interaction.events import PresenceEvent, PresenceEventType


def test_turn_manager_speaker_inference():
    manager = TurnManager()

    # 1. Doctor
    event_doc = PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="Face_Doc",
        name="Dr. Smith",
        relationship="Doctor",
    )
    assert manager.determine_speaker_from_event(event_doc) == SpeakerRole.DOCTOR

    # 2. Caregiver
    event_care = PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="Face_Nurse",
        name="Mary",
        relationship="Caregiver",
    )
    assert manager.determine_speaker_from_event(event_care) == SpeakerRole.CAREGIVER

    # 3. Visitor
    event_vis = PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="Face_1",
        name="Sarah",
        relationship="Daughter",
    )
    assert manager.determine_speaker_from_event(event_vis) == SpeakerRole.VISITOR

    # 4. Patient
    event_patient = PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="Face_Self",
        name="Patient",
        relationship=None,
    )
    assert manager.determine_speaker_from_event(event_patient) == SpeakerRole.PATIENT
