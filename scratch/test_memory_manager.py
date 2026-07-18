import os
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.memory.database import MemoraDatabase
from src.cognition.episode import Episode
from src.cognition.cognitive_memory_manager import CognitiveMemoryManager
from src.llm.reasoning_client import ReasoningClient
from src.memory.models import SemanticNodeModel

class FakeJSONReasoningClient(ReasoningClient):
    """
    Mocks the LLM fact extraction to return strict JSON for testing.
    """
    def generate_cue(self, structured_prompt: str) -> str:
        # We always return this mock JSON array of facts for testing
        return '''
        [
            {"subject": "Sarah", "predicate": "visits_on", "object": "tuesday", "category": "ROUTINE", "importance": 2},
            {"subject": "Sarah", "predicate": "favorite_color", "object": "blue", "category": "PREFERENCE", "importance": 1},
            {"subject": "Sarah", "predicate": "needs_medication", "object": "heart_pills", "category": "MEDICAL", "importance": 4}
        ]
        '''

def main():
    print("Testing Milestone 5: Cognitive Memory Manager...\n")
    
    # 1. Setup
    db = MemoraDatabase()
    db.clear()
    
    manager = CognitiveMemoryManager(db.SessionFactory, FakeJSONReasoningClient())
    
    print("1. Creating Episode 1 (Simulating Sarah visiting)...")
    ep1 = Episode(person="Sarah", summary="Sarah visited on Tuesday. She likes blue.", timestamp=datetime.now())
    manager.consolidator.consolidate(ep1)
    
    print("2. Creating Episode 2 (Simulating Sarah visiting again, reinforcing knowledge)...")
    ep2 = Episode(person="Sarah", summary="Sarah visited on Tuesday again.", timestamp=datetime.now())
    manager.consolidator.consolidate(ep2)
    
    # Check DB for created Semantic Nodes
    with db.SessionFactory() as session:
        nodes = session.query(SemanticNodeModel).all()
        print(f"\nKnowledge Graph created {len(nodes)} semantic nodes:")
        for n in nodes:
            print(f"- {n.subject} {n.predicate} {n.object_val} (Cat: {n.category}, Imp: {n.importance}, Conf: {n.confidence:.2f})")
            
            # Since we consolidated twice, confidence should be bumped from 0.8 to 1.0!
            assert n.confidence == 1.0, f"Confidence was not reinforced! Got {n.confidence}"
            
    print("\n3. Simulating 10 days of decay...")
    future_time = datetime.now() + timedelta(days=10)
    manager.forgetting_strategy.decay_memories(current_time=future_time)
    
    with db.SessionFactory() as session:
        nodes = session.query(SemanticNodeModel).all()
        print("\nKnowledge Graph after 10 days of decay:")
        for n in nodes:
            print(f"- {n.subject} {n.predicate} {n.object_val} (Conf: {n.confidence:.2f})")
            
            if n.category == "MEDICAL":
                assert n.confidence == 1.0, "Medical memory incorrectly decayed!"
            elif n.category == "PREFERENCE":
                assert n.confidence < 1.0, "Preference memory failed to decay!"
                
    print("\nMilestone 5 Test Passed Successfully!")
    manager.shutdown()

if __name__ == "__main__":
    main()
