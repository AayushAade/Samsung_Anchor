from typing import Protocol, Any, Optional
from dataclasses import dataclass
from src.interaction.events import PresenceEvent
from src.cognition.context.models import ContextFreshness

@dataclass
class ProviderResponse:
    domain: str
    data: Any
    confidence: float
    freshness: ContextFreshness
    latency_ms: float
    is_missing: bool = False
    error: Optional[str] = None

class ContextProvider(Protocol):
    """
    Standard interface for all Context Providers.
    """
    @property
    def name(self) -> str:
        ...
        
    @property
    def capability_domain(self) -> str:
        """e.g., 'identity', 'memory', 'temporal'"""
        ...
        
    def fetch_context(self, event: PresenceEvent) -> ProviderResponse:
        """
        Fetches context synchronously. The ContextFusionEngine will handle 
        wrapping these in a ThreadPoolExecutor for concurrent execution.
        """
        ...
