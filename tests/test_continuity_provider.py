from datetime import datetime

from src.cognition.context.providers.continuity import ContinuityContextProvider
from src.interaction.events import PresenceEvent, PresenceEventType


def test_continuity_provider_name_and_domain():
    provider = ContinuityContextProvider()
    assert provider.name == "ContinuityContextProvider"
    assert provider.capability_domain == "continuity"


def test_continuity_provider_fetch_context():
    provider = ContinuityContextProvider()
    event = PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="Face_1",
        name="Sarah",
        relationship="Daughter",
    )

    response = provider.fetch_context(event)

    assert response is not None
    assert response.domain == "continuity"
    assert response.confidence == 0.95
    assert response.is_missing is False

    data = response.data
    assert data is not None
    assert hasattr(data, "routine_stage")
    assert hasattr(data, "current_day")
    assert hasattr(data, "approximate_time")
    assert hasattr(data, "recent_activity")
    assert hasattr(data, "upcoming_activity")
    assert isinstance(data.today_events, list)
