import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.memory.database import MemoraDatabase
from src.cognition.conversation import Conversation
from src.cognition.episode_builder import EpisodeBuilder
from src.cognition.episode_engine import EpisodeEngine
from src.pipeline.cognitive_pipeline import CognitivePipeline

def main():
    print("Testing Milestone 3: True Episodic Memory...")
    
    # 1. Initialize DB
    db = MemoraDatabase()
    db.clear()
    
    # 2. Simulate Identity Learning saving an Episode
    print("1. Simulating an identity learning conversation...")
    engine = EpisodeEngine(
        builder=EpisodeBuilder(),
        repository=db.episode_repo
    )
    
    conversation = Conversation(
        person="Sarah",
        transcript="Hi, I am your daughter Sarah. I brought your favorite cookies.",
        summary="Sarah visited and brought cookies.",
        commitments=["Eat cookies later"]
    )
    
    episode = engine.remember(conversation)
    print(f"Saved Episode to DB: {episode.summary}")
    
    # 3. Simulate Vision detecting Sarah
    print("\n2. Simulating vision detecting Sarah...")
    pipeline = CognitivePipeline(db)
    
    # Normally PresenceEngine relies on face_id (Anonymous_ID_X) or name if confirmed.
    # In this mock, we pass name='Sarah' to ensure PresenceEngine creates an event.
    result = {
        "face_id": "Face_1",
        "name": "Sarah",
        "relationship": "Daughter"
    }
    
    actions = pipeline.process(result)
    
    print("\n3. Cognitive Pipeline Results:")
    for a in actions:
        print(f"Action generated: {a.message}")
        
    # Let's directly check MemoryEngine retrieval
    from src.cognition.memory_query import MemoryQuery
    memories = pipeline.memory_engine.retrieve(MemoryQuery(face_id="Sarah"))
    
    print(f"\nRetrieved {len(memories)} memories for Sarah from the DB:")
    for m in memories:
        print(f"- Type: {m.memory_type.value}, Summary: {m.summary}, Commitments: {m.commitments}")
        assert "cookies" in m.summary, "Memory retrieval failed!"
        
    print("\nMilestone 3 Test Passed Successfully!")

if __name__ == "__main__":
    main()
