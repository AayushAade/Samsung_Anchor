import time
from src.cognition.context.provider import ContextProvider, ProviderResponse
from src.interaction.events import PresenceEvent
from src.cognition.context.models import IdentityContext, ContextFreshness

class IdentityContextProvider:
    """
    Extracts identity context directly from the PresenceEvent.
    In the future, this could fuse face ID with voice biometrics.
    """
    @property
    def name(self) -> str:
        return "IdentityContextProvider"
        
    @property
    def capability_domain(self) -> str:
        return "identity"
        
    def fetch_context(self, event: PresenceEvent) -> ProviderResponse:
        start_t = time.perf_counter()
        
        ctx = IdentityContext(
            face_id=event.face_id,
            name=event.name,
            relationship=event.relationship,
            confidence=1.0, # Default to 1.0 since PresenceEvent doesn't store confidence
            is_known=event.name is not None
        )
        
        return ProviderResponse(
            domain=self.capability_domain,
            data=ctx,
            confidence=1.0,
            freshness=ContextFreshness.REALTIME,
            latency_ms=(time.perf_counter() - start_t) * 1000
        )
