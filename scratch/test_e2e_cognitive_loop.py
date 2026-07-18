import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline
from src.core.metrics import metrics
from src.core.inspector import CognitiveInspector

# To mock identity learning:
from src.cognition.episode import Episode
from src.cognition.cognitive_memory_manager import CognitiveMemoryManager
from src.llm.reasoning_client import MockReasoningClient, ReasoningClient

class FakeJSONReasoningClient(ReasoningClient):
    def generate_cue(self, structured_prompt: str) -> str:
        if "Extract" in structured_prompt or "extract" in structured_prompt:
            return '''[
                {"subject": "Sarah", "predicate": "needs_medication", "object": "heart_pills", "category": "MEDICAL", "importance": 4}
            ]'''
        return "Sarah reminded to take heart medication."

def main():
    print("==================================================")
    print("  Testing Milestone 7: End-to-End Cognitive Loop  ")
    print("==================================================")
    
    # 1. Initialize
    db = MemoraDatabase()
    db.clear()
    
    pipeline = CognitivePipeline(db)
    # Ensure it's using the Mock Client so tests pass without API keys
    pipeline.context_restoration_engine.client = FakeJSONReasoningClient()
    
    manager = CognitiveMemoryManager(db.SessionFactory, FakeJSONReasoningClient())
    
    # Register "Sarah"
    face_id = "Face_1"
    db.bind_name(face_id, "Sarah", "Daughter")

    # ---------------------------------------------------------
    # Scenario A: Initial Detection (No Memories)
    # ---------------------------------------------------------
    print("\n[Scenario A] Detecting Sarah (No memories yet)")
    recognition_result = {
        "face_id": face_id,
        "name": "Sarah",
        "relationship": "Daughter",
        "confidence": 0.99
    }
    
    # Run the entire pipeline
    actions = pipeline.process(recognition_result)
    
    # Expected: The pipeline should have aborted at the Attention Engine (Threshold)
    # resulting in zero actions (Silence) or just the basic presence.
    # Wait, the PresenceEngine returns the event.
    # The MemoryEngine finds 0 memories.
    # AttentionEngine returns Silence.
    # InteractionManager returns None if Silence.
    assert len(actions) == 0, f"Expected silence, but got actions: {actions}"
    
    # ---------------------------------------------------------
    # Scenario B: Identity Learning (Background Consolidation)
    # ---------------------------------------------------------
    print("\n[Scenario B] Simulating a Conversation...")
    # Simulate Episode Engine saving an episode
    ep = Episode(person=face_id, summary="Sarah reminded to take heart medication.", commitments=["Take heart pill"], timestamp=datetime.now())
    # Save manually since EpisodeEngine isn't wired to DB in this standalone script
    with db.SessionFactory() as session:
        from src.memory.models import EpisodeModel
        session.add(EpisodeModel(person=face_id, summary=ep.summary, timestamp=ep.timestamp.isoformat(), commitments=ep.commitments))
        session.commit()
    
    # Simulate the memory manager consolidating the episode into Semantic graph
    manager.process_episode(ep)
    manager.executor.shutdown(wait=True) # Wait for it to finish
    
    # ---------------------------------------------------------
    # Scenario C: Detection with Urgent Memory
    # ---------------------------------------------------------
    print("\n[Scenario C] Detecting Sarah again (With Urgent Memory)")
    # Recreate a fresh manager to restart executor if we needed it, but we only ran it once.
    pipeline.reset()
    
    # Run the pipeline again
    actions = pipeline.process(recognition_result)
    print(f"[DEBUG] Actions returned: {actions}")
    
    assert len(actions) == 1, "Expected 1 action (SPEAK) due to Urgent Memory"
    print(f"\nFinal Generated Action: '{actions[0].message}'")
    
    # ---------------------------------------------------------
    # Observability Output
    # ---------------------------------------------------------
    print("\n" + metrics.summary())
    print("End-to-End Test Passed!")

if __name__ == "__main__":
    main()
