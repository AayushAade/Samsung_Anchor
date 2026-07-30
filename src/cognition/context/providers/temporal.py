import time
from datetime import datetime
from src.cognition.context.provider import ContextProvider, ProviderResponse
from src.interaction.events import PresenceEvent
from src.cognition.context.models import TemporalContext, ContextFreshness

class TemporalContextProvider:
    """
    Provides real-time temporal context (time, day, semantic time of day).
    """
    @property
    def name(self) -> str:
        return "TemporalContextProvider"
        
    @property
    def capability_domain(self) -> str:
        return "temporal"
        
    def _get_time_of_day(self, hour: int) -> str:
        if 5 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 17:
            return "Afternoon"
        elif 17 <= hour < 21:
            return "Evening"
        else:
            return "Night"
            
    def fetch_context(self, event: PresenceEvent) -> ProviderResponse:
        start_t = time.perf_counter()
        
        now = datetime.now()
        
        ctx = TemporalContext(
            current_time=now,
            time_of_day=self._get_time_of_day(now.hour),
            day_of_week=now.strftime("%A"),
            confidence=1.0
        )
        
        return ProviderResponse(
            domain=self.capability_domain,
            data=ctx,
            confidence=1.0,
            freshness=ContextFreshness.REALTIME,
            latency_ms=(time.perf_counter() - start_t) * 1000
        )
