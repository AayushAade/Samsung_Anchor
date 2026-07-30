import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cognition.context.registry import ContextProviderRegistry
from src.cognition.context.fusion_engine import ContextFusionEngine
from src.cognition.context.providers.identity import IdentityContextProvider
from src.cognition.context.providers.temporal import TemporalContextProvider
from src.interaction.events import PresenceEvent
from src.core.inspector import CognitiveInspector

class MockSlowProvider:
    @property
    def name(self): return "SlowProvider"
    @property
    def capability_domain(self): return "mock"
    def fetch_context(self, event):
        time.sleep(1.0) # Will cause timeout
        return None

def main():
    print("==================================================")
    print("  Testing Phase 2: Context Fusion Framework       ")
    print("==================================================")
    
    registry = ContextProviderRegistry()
    registry.register(IdentityContextProvider())
    registry.register(TemporalContextProvider())
    registry.register(MockSlowProvider())
    
    # Timeout is set to 0.5s, so the SlowProvider should be dropped
    fusion_engine = ContextFusionEngine(registry, timeout_sec=0.5)
    
    from src.interaction.events import PresenceEventType
    event = PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="Face_Sarah",
        name="Sarah",
        relationship="Daughter"
    )
    
    print("\n[Test] Executing Context Fusion...")
    
    cognitive_context = fusion_engine.fuse_context(event)
    
    # Print the trace
    from src.cognition.attention.attention_models import AttentionDecision
    # Mocking attention decision since we're just testing Context Generation
    dummy_decision = AttentionDecision(should_interrupt=False, selected_memories=[])
    
    CognitiveInspector.print_pipeline_run(
        cognitive_context=cognitive_context,
        attention_decision=dummy_decision
    )
    
    # Assertions
    assert cognitive_context.identity is not None
    assert cognitive_context.identity.name == "Sarah"
    assert cognitive_context.temporal is not None
    assert "SlowProvider" in cognitive_context.dropped_providers
    print("\n[Result] Context Fusion Engine completed successfully and gracefully degraded the slow provider!")

if __name__ == "__main__":
    main()
