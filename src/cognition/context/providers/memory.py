import time
from src.cognition.context.provider import ContextProvider, ProviderResponse
from src.interaction.events import PresenceEvent
from src.cognition.context.models import MemoryContext, ContextFreshness
from src.cognition.memory_engine import MemoryEngine
from src.cognition.memory_query import MemoryQuery

class MemoryContextProvider:
    """
    Retrieves Episodic and Semantic memories related to the detected face.
    """
    def __init__(self, memory_engine: MemoryEngine):
        self.memory_engine = memory_engine

    @property
    def name(self) -> str:
        return "MemoryContextProvider"
        
    @property
    def capability_domain(self) -> str:
        return "memory"
        
    def fetch_context(self, event: PresenceEvent) -> ProviderResponse:
        start_t = time.perf_counter()
        
        query = MemoryQuery(face_id=event.face_id)
        memories = self.memory_engine.retrieve(query)
        
        ctx = MemoryContext(
            memories=memories,
            confidence=1.0 # High confidence that these are the stored memories
        )
        
        return ProviderResponse(
            domain=self.capability_domain,
            data=ctx,
            confidence=1.0,
            freshness=ContextFreshness.ARCHIVED,
            latency_ms=(time.perf_counter() - start_t) * 1000,
            is_missing=len(memories) == 0
        )
