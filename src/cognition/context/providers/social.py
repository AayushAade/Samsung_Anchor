import time
from typing import Optional

from src.cognition.context.models import ContextFreshness
from src.cognition.context.provider import ContextProvider, ProviderResponse
from src.cognition.relationships.manager import RelationshipManager
from src.cognition.relationships.models import SocialContext
from src.interaction.events import PresenceEvent


class SocialContextProvider(ContextProvider):
    """
    Context Provider for Preserving Human Connections and Relationship Intelligence.
    Retrieves rich relationship profiles, visitor context, and shared memories.
    """

    def __init__(self, relationship_manager: Optional[RelationshipManager] = None) -> None:
        self.relationship_manager = relationship_manager or RelationshipManager()

    @property
    def name(self) -> str:
        return "SocialContextProvider"

    @property
    def capability_domain(self) -> str:
        return "social"

    def fetch_context(self, event: PresenceEvent) -> ProviderResponse:
        start_t = time.perf_counter()

        profile = None
        if event.face_id or event.name or event.relationship:
            profile = self.relationship_manager.get_profile(
                person_id=event.face_id or "unknown",
                name=event.name,
                relationship=event.relationship,
            )

        social_ctx = SocialContext(
            active_profile=profile,
            known_relationships_count=1 if profile else 0,
            confidence=1.0 if profile else 0.5,
        )

        return ProviderResponse(
            domain=self.capability_domain,
            data=social_ctx,
            confidence=1.0 if profile else 0.5,
            freshness=ContextFreshness.REALTIME,
            latency_ms=(time.perf_counter() - start_t) * 1000,
        )
