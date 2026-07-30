"""
Samsung Anchor — Context Restoration Engine Test (Modernized for Phase 2+).

Tests the full context restoration pipeline using CognitiveContext.
"""

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cognition.memory_models import RelevantMemory, MemoryType, MemoryImportance
from src.cognition.context_restoration_engine import ContextRestorationEngine
from src.cognition.context.models import (
    CognitiveContext, IdentityContext, MemoryContext, TemporalContext,
)


def main():
    print("Testing Context Restoration Engine (Phase 2+ API)...\n")

    now = datetime.now()

    # Build a CognitiveContext with medical memories that should trigger INTERRUPT
    ctx = CognitiveContext(
        timestamp=now,
        identity=IdentityContext(
            face_id="Face_1", name="Sarah", relationship="Daughter",
            confidence=1.0, is_known=True,
        ),
        memory=MemoryContext(
            memories=[
                RelevantMemory(
                    memory_id="2",
                    memory_type=MemoryType.EPISODIC,
                    importance=MemoryImportance.HIGH,
                    summary="Sarah mentioned her new dog.",
                    timestamp=now - timedelta(hours=2),
                    commitments=["Ask about dog"],
                ),
                RelevantMemory(
                    memory_id="4",
                    memory_type=MemoryType.SEMANTIC,
                    importance=MemoryImportance.CRITICAL,
                    summary="Sarah reminded to take heart medication.",
                    timestamp=now - timedelta(days=1),
                ),
            ],
            confidence=1.0,
        ),
        temporal=TemporalContext(
            current_time=now, time_of_day="Afternoon",
            day_of_week="Monday", confidence=1.0,
        ),
    )

    engine = ContextRestorationEngine()

    # Run the full pipeline
    recall = engine.generate_context_cue(cognitive_context=ctx)

    print(f"Should Greet : {recall.should_greet}")
    print(f"Memories Used: {len(recall.recalled_memories) if recall.recalled_memories else 0}")
    print(f"LLM Response : '{recall.generated_response}'")

    assert recall.should_greet, "Should have chosen to greet (medical memory present)"
    assert recall.recalled_memories, "Should have selected memories"

    print("\nContext Restoration Engine Test Passed!")


if __name__ == "__main__":
    main()
