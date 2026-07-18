from typing import List, Dict, Optional
from src.cognition.context.provider import ContextProvider

class ContextProviderRegistry:
    """
    Service locator for Context Providers.
    Tracks health, availability, and routing.
    """
    def __init__(self):
        self._providers: Dict[str, ContextProvider] = {}
        self._disabled: set = set()
        
    def register(self, provider: ContextProvider) -> None:
        self._providers[provider.name] = provider
        print(f"[ContextRegistry] Registered Provider: {provider.name} ({provider.capability_domain})")
        
    def disable(self, provider_name: str) -> None:
        self._disabled.add(provider_name)
        
    def enable(self, provider_name: str) -> None:
        if provider_name in self._disabled:
            self._disabled.remove(provider_name)
            
    def get_active_providers(self) -> List[ContextProvider]:
        return [p for name, p in self._providers.items() if name not in self._disabled]
