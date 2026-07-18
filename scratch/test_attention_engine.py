import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cognition.attention.attention_engine import CognitiveAttentionEngine
from src.cognition.attention.attention_models import CognitiveState
from src.cognition.memory_models import RelevantMemory, MemoryImportance, MemoryType
from src.interaction.events import PresenceEvent, PresenceEventType

def main():
    print("Testing Milestone 6: Cognitive Attention Engine...\n")
    
    engine = CognitiveAttentionEngine(max_attention_items=3)
    
    now = datetime.now()
    state = CognitiveState(
        current_time=now,
        current_location="Living Room",
        face_id="Face_1",
        name="Sarah",
        relationship="Daughter"
    )

    # ---------------------------------------------------------
    # Scenario 1: Trivial Memory (Should Result in Silence)
    # ---------------------------------------------------------
    print("--- SCENARIO 1: Trivial Memory ---")
    memories_trivial = [
        RelevantMemory(
            memory_id="1",
            memory_type=MemoryType.SEMANTIC,
            importance=MemoryImportance.LOW, # Base: 10
            summary="Sarah likes blue.",
            timestamp=now - timedelta(days=10) # Recency: ~1.3
        )
    ]
    
    decision_1 = engine.evaluate(memories_trivial, state)
    assert not decision_1.should_interrupt, "System should be silent for trivial memory!"
    print("Result: SUCCESS (System chose SILENCE)\n")

    # ---------------------------------------------------------
    # Scenario 2: Medical / Commitment (Should Result in Interrupt)
    # ---------------------------------------------------------
    print("--- SCENARIO 2: Medical / Commitment Memory ---")
    memories_urgent = [
        RelevantMemory(
            memory_id="2",
            memory_type=MemoryType.EPISODIC,
            importance=MemoryImportance.HIGH, # Base: 30
            summary="Sarah reminded to take heart medicine.",
            timestamp=now - timedelta(hours=2), # Recency: ~14
            commitments=["Take pill"] # Commitment: +25, Medical: +20
        ),
        RelevantMemory(
            memory_id="3",
            memory_type=MemoryType.SEMANTIC,
            importance=MemoryImportance.LOW,
            summary="Sarah likes blue.",
            timestamp=now - timedelta(days=10)
        )
    ]
    
    decision_2 = engine.evaluate(memories_urgent, state)
    assert decision_2.should_interrupt, "System should interrupt for medical commitment!"
    assert len(decision_2.selected_memories) == 2, "Should select both memories but rank medical first"
    assert decision_2.selected_memories[0].memory_id == "2", "Urgent memory should be ranked first"
    print("Result: SUCCESS (System chose INTERRUPT and correctly ranked urgency)\n")
    
    print("Milestone 6 Test Passed Successfully!")

if __name__ == "__main__":
    main()
