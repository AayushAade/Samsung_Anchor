from src.cognition.context.providers.social import SocialContextProvider
from src.interaction.events import PresenceEvent, PresenceEventType


def test_social_provider_name_and_domain():
    provider = SocialContextProvider()
    assert provider.name == "SocialContextProvider"
    assert provider.capability_domain == "social"


def test_social_provider_fetch_context_known():
    provider = SocialContextProvider()
    event = PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="Face_1",
        name="Sarah",
        relationship="Daughter",
    )

    response = provider.fetch_context(event)

    assert response is not None
    assert response.domain == "social"
    assert response.confidence == 1.0

    social_data = response.data
    assert social_data is not None
    assert social_data.active_profile is not None
    assert social_data.active_profile.name == "Sarah"
    assert len(social_data.active_profile.shared_memories) > 0


def test_social_provider_fetch_context_unknown():
    provider = SocialContextProvider()
    event = PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="Face_Unknown",
        name=None,
        relationship=None,
    )

    response = provider.fetch_context(event)

    assert response is not None
    assert response.domain == "social"
    assert response.data.active_profile is None
