import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cognition.memory_models import RelevantMemory, MemoryType, MemoryImportance
from src.interaction.events import PresenceEvent, PresenceEventType
from src.cognition.context_restoration_engine import ContextRestorationEngine

def main():
    print("Testing Milestone 4: Context Restoration Engine...\n")
    
    # 1. Setup Mock Event
    event = PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="Face_1",
        name="Sarah",
        relationship="Daughter"
    )
    
    # 2. Setup Mock Memories
    now = datetime.now()
    memories = [
        # Very old memory (should be ranked lower)
        RelevantMemory(
            memory_id="1",
            memory_type=MemoryType.EPISODIC,
            importance=MemoryImportance.NORMAL,
            summary="Sarah visited and we watched TV.",
            timestamp=now - timedelta(days=30)
        ),
        # Recent memory with commitments (should rank very high)
        RelevantMemory(
            memory_id="2",
            memory_type=MemoryType.EPISODIC,
            importance=MemoryImportance.HIGH,
            summary="Sarah mentioned her new dog.",
            timestamp=now - timedelta(hours=2),
            commitments=["Ask about dog"]
        ),
        # Trivial memory
        RelevantMemory(
            memory_id="3",
            memory_type=MemoryType.SEMANTIC,
            importance=MemoryImportance.LOW,
            summary="Sarah likes blue.",
            timestamp=now - timedelta(days=5)
        ),
        # Medical memory
        RelevantMemory(
            memory_id="4",
            memory_type=MemoryType.SEMANTIC,
            importance=MemoryImportance.CRITICAL,
            summary="Sarah reminded to take heart medication.",
            timestamp=now - timedelta(days=1)
        )
    ]
    
    # 3. Run Engine
    engine = ContextRestorationEngine()
    
    # Print the raw prompt generation to verify structure
    prompt = engine.builder.build_prompt(
        event=event,
        memories=engine.ranker.rank(memories),
        current_location="Living Room",
        current_time="4:30 PM"
    )
    
    print("--- GENERATED PROMPT SENT TO LLM ---")
    print(prompt)
    print("------------------------------------\n")
    
    # 4. End-to-end Pipeline Test
    recall = engine.generate_context_cue(
        event=event,
        raw_memories=memories,
        current_location="Living Room",
        current_time="4:30 PM"
    )
    
    print(f"Engine returned generated response: '{recall.generated_response}'")
    
    print("\nMilestone 4 Engine Test Passed!")

if __name__ == "__main__":
    main()
