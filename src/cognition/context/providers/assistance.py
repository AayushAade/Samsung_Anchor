import time
from typing import Optional

from src.cognition.assistance.policy_engine import AssistancePolicyEngine
from src.cognition.context.models import ContextFreshness
from src.cognition.context.provider import ContextProvider, ProviderResponse
from src.interaction.events import PresenceEvent


class AssistanceContextProvider(ContextProvider):
    """
    Context Provider for Graduated Assistance and Preserving Independence.
    Deterministically evaluates minimum effective assistance level (Level 0 - Level 5).
    """

    def __init__(self, policy_engine: Optional[AssistancePolicyEngine] = None) -> None:
        self.policy_engine = policy_engine or AssistancePolicyEngine()

    @property
    def name(self) -> str:
        return "AssistanceContextProvider"

    @property
    def capability_domain(self) -> str:
        return "assistance"

    def fetch_context(self, event: PresenceEvent) -> ProviderResponse:
        start_t = time.perf_counter()

        has_mem = bool(event.name or event.relationship)
        has_medical = bool(event.relationship and "Daughter" in event.relationship)

        assistance_data = self.policy_engine.evaluate_level(
            event=event,
            has_medical_commitment=has_medical,
            has_active_goals=True,
            has_known_memories=has_mem,
        )

        return ProviderResponse(
            domain=self.capability_domain,
            data=assistance_data,
            confidence=1.0,
            freshness=ContextFreshness.REALTIME,
            latency_ms=(time.perf_counter() - start_t) * 1000,
        )
