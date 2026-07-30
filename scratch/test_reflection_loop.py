import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.memory.database import MemoraDatabase
from src.memory.models import InteractionRecordModel, SemanticNodeModel
from src.cognition.reflection.feedback import FeedbackEvent, FeedbackType, FeedbackSource
from src.cognition.reflection.reflection_engine import ReflectionEngine
from src.core.inspector import CognitiveInspector

def main():
    print("==================================================")
    print("  Testing Milestone 8: Meta-Cognitive Reflection  ")
    print("==================================================")
    
    db = MemoraDatabase()
    db.clear()
    
    # 1. Setup a Semantic Node (e.g., from a past consolidation)
    with db.SessionFactory() as session:
        node = SemanticNodeModel(
            subject="Sarah",
            predicate="favorite_color",
            object_val="blue",
            category="PREFERENCE",
            importance=2, # NORMAL
            confidence=1.0,
            last_reinforced=datetime.now().isoformat(),
            historical_usefulness=0.5 # Default
        )
        session.add(node)
        session.commit()
        node_id = node.id
        
    print(f"\n[Setup] Created Semantic Node ID: {node_id} (Confidence: 1.0, Usefulness: 0.5)")
        
    # 2. Simulate an Interaction Record where we used this node
    with db.SessionFactory() as session:
        interaction = InteractionRecordModel(
            timestamp=datetime.now().isoformat(),
            face_id="Face_1",
            decision="INTERRUPT",
            selected_memory_ids=[f"sem_{node_id}"],
            prompt_sent="Mock prompt",
            generated_response="Sarah, is your favorite color still blue?"
        )
        session.add(interaction)
        session.commit()
        interaction_id = interaction.id
        
    print(f"[Setup] Logged Interaction ID: {interaction_id} using Semantic Node {node_id}")
        
    # 3. Simulate a Feedback Event (Correction)
    print("\n[Event] Sarah replies: 'No, my favorite color is green now.'")
    event = FeedbackEvent(
        interaction_id=interaction_id,
        source=FeedbackSource.VOICE,
        feedback_type=FeedbackType.CORRECTION,
        content="No, my favorite color is green now.",
        timestamp=datetime.now().isoformat()
    )
    
    # 4. Run Reflection Engine
    engine = ReflectionEngine(db.SessionFactory)
    print("[ReflectionEngine] Submitting FeedbackEvent...")
    engine.process_feedback(event)
    
    # Wait for background thread
    engine.executor.shutdown(wait=True)
    
    # 5. Verify the updates
    print("\n[Verification] Checking Semantic Node state...")
    with db.SessionFactory() as session:
        updated_node = session.query(SemanticNodeModel).filter_by(id=node_id).first()
        print(f"  -> Correction Count: {updated_node.correction_count} (Expected: 1)")
        print(f"  -> Confidence: {updated_node.confidence:.2f} (Expected: 0.50)")
        print(f"  -> Historical Usefulness: {updated_node.historical_usefulness:.2f} (Expected: 0.20)")
        print(f"  -> Verification Status: {updated_node.verification_status} (Expected: Corrected)")
        
        assert updated_node.correction_count == 1
        assert updated_node.confidence == 0.5
        # 0.5 - 0.3 = 0.2
        assert abs(updated_node.historical_usefulness - 0.2) < 0.001
        
    print("\nMeta-Cognition Test Passed Successfully!")

if __name__ == "__main__":
    main()
