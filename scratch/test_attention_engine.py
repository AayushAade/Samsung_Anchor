"""
Samsung Anchor — Attention Engine Test (Modernized for Phase 2+).

Tests the CognitiveAttentionEngine using CognitiveContext (not raw memories + state).
"""

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cognition.attention.attention_engine import CognitiveAttentionEngine
from src.cognition.context.models import (
    CognitiveContext, IdentityContext, MemoryContext, TemporalContext,
)
from src.cognition.memory_models import RelevantMemory, MemoryImportance, MemoryType


def main():
    print("Testing Attention Engine (Phase 2 API)...\n")

    engine = CognitiveAttentionEngine(max_attention_items=3)
    now = datetime.now()

    # ---------------------------------------------------------
    # Scenario 1: Trivial Memory (Should Result in Silence)
    # ---------------------------------------------------------
    print("--- SCENARIO 1: Trivial Memory ---")
    ctx_trivial = CognitiveContext(
        timestamp=now,
        identity=IdentityContext(
            face_id="Face_1", name="Sarah", relationship="Daughter",
            confidence=1.0, is_known=True
        ),
        memory=MemoryContext(
            memories=[
                RelevantMemory(
                    memory_id="1",
                    memory_type=MemoryType.SEMANTIC,
                    importance=MemoryImportance.LOW,
                    summary="Sarah likes blue.",
                    timestamp=now - timedelta(days=10)
                )
            ],
            confidence=1.0,
        ),
        temporal=TemporalContext(
            current_time=now, time_of_day="Afternoon",
            day_of_week="Monday", confidence=1.0
        ),
    )

    decision_1 = engine.evaluate(ctx_trivial)
    assert not decision_1.should_interrupt, "System should be silent for trivial memory!"
    print("Result: SUCCESS (System chose SILENCE)\n")

    # ---------------------------------------------------------
    # Scenario 2: Medical / Commitment (Should Result in Interrupt)
    # ---------------------------------------------------------
    print("--- SCENARIO 2: Medical / Commitment Memory ---")
    ctx_urgent = CognitiveContext(
        timestamp=now,
        identity=IdentityContext(
            face_id="Face_1", name="Sarah", relationship="Daughter",
            confidence=1.0, is_known=True
        ),
        memory=MemoryContext(
            memories=[
                RelevantMemory(
                    memory_id="2",
                    memory_type=MemoryType.EPISODIC,
                    importance=MemoryImportance.HIGH,
                    summary="Sarah reminded to take heart medicine.",
                    timestamp=now - timedelta(hours=2),
                    commitments=["Take pill"]
                ),
                RelevantMemory(
                    memory_id="3",
                    memory_type=MemoryType.SEMANTIC,
                    importance=MemoryImportance.LOW,
                    summary="Sarah likes blue.",
                    timestamp=now - timedelta(days=10)
                )
            ],
            confidence=1.0,
        ),
        temporal=TemporalContext(
            current_time=now, time_of_day="Morning",
            day_of_week="Monday", confidence=1.0
        ),
    )

    decision_2 = engine.evaluate(ctx_urgent)
    assert decision_2.should_interrupt, "System should interrupt for medical commitment!"
    assert len(decision_2.selected_memories) == 2, "Should select both memories"
    assert decision_2.selected_memories[0].memory_id == "2", "Urgent memory should be ranked first"
    print("Result: SUCCESS (System chose INTERRUPT and correctly ranked urgency)\n")

    print("Attention Engine Test Passed Successfully!")


if __name__ == "__main__":
    main()
