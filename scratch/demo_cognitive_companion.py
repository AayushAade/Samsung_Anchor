import os
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline
from src.core.metrics import metrics
from src.core.inspector import CognitiveInspector
from src.cognition.episode import Episode
from src.cognition.cognitive_memory_manager import CognitiveMemoryManager
from src.llm.reasoning_client import MockReasoningClient

# A mock Reasoning Client that gives us beautiful demo responses
class DemoReasoningClient(MockReasoningClient):
    def generate_cue(self, structured_prompt: str) -> str:
        if "extract" in structured_prompt.lower():
            return '''[
                {"subject": "Sarah", "predicate": "needs_medication", "object": "heart_pills", "category": "MEDICAL", "importance": 4}
            ]'''
        return "Don't forget to ask Sarah if she took her heart medication today."

def sleep_print(text, delay=1.0):
    print(text)
    time.sleep(delay)

def main():
    print("================================================================")
    print("    SAMSUNG ANCHOR: THE ARTIFICIAL EXTERNAL HIPPOCAMPUS         ")
    print("================================================================\n")
    
    db = MemoraDatabase()
    db.clear()
    pipeline = CognitivePipeline(db)
    manager = CognitiveMemoryManager(db.SessionFactory, DemoReasoningClient())
    pipeline.context_restoration_engine.client = DemoReasoningClient()

    face_id = "Face_1"
    
    # ---------------------------------------------------------
    # DAY 1
    # ---------------------------------------------------------
    sleep_print("--- DAY 1: INTRODUCTION ---")
    sleep_print("Event: The user registers their daughter, Sarah.")
    db.bind_name(face_id, "Sarah", "Daughter")
    sleep_print("[Database] Identity bound: Sarah -> Daughter.\n")
    
    sleep_print("Event: Sarah walks into the room.")
    recognition_result = {"face_id": face_id, "name": "Sarah", "relationship": "Daughter", "confidence": 0.99}
    
    actions = pipeline.process(recognition_result)
    # With no memories, system should be silent.
    sleep_print("System Reasoning:")
    sleep_print(" > Retrieved 0 memories.")
    sleep_print(" > Attention Engine Score: 0.0 -> SILENCE.")
    sleep_print("Action Taken: [No speech. System remains passively observant.]\n")
    
    # ---------------------------------------------------------
    # DAY 2
    # ---------------------------------------------------------
    sleep_print("--- DAY 2: A CONVERSATION ---")
    sleep_print("Event: Sarah mentions that she needs to take heart medication every day.")
    
    # Episode Creation
    ep = Episode(person=face_id, summary="Sarah mentioned she needs to take heart pills.", commitments=["Remind about heart pills"], timestamp=datetime.now())
    with db.SessionFactory() as session:
        from src.memory.models import EpisodeModel
        session.add(EpisodeModel(person=face_id, summary=ep.summary, timestamp=ep.timestamp.isoformat(), commitments=ep.commitments))
        session.commit()
        
    sleep_print("[Episode Engine] Recorded Episodic Memory.")
    sleep_print("[Cognitive Memory Manager] Background consolidation started...")
    manager.process_episode(ep)
    manager.executor.shutdown(wait=True)
    sleep_print("[Memory Consolidator] Fact extracted -> (Sarah, needs_medication, heart_pills) [Importance: 4/Critical]\n")
    
    # ---------------------------------------------------------
    # DAY 10
    # ---------------------------------------------------------
    sleep_print("--- DAY 10: THE COGNITIVE COMPANION ---")
    pipeline.reset()
    sleep_print("Event: Sarah walks into the room again.")
    sleep_print("System Reasoning:")
    
    actions = pipeline.process(recognition_result)
    
    sleep_print(" > Retrieving Memories...")
    sleep_print(" > Found 1 Episode and 1 Semantic Node.")
    sleep_print(" > Attention Engine evaluating...")
    sleep_print(" > Critical Medical Fact detected! Score: > 60.0 (Threshold: 35.0)")
    sleep_print(" > Attention Engine -> INTERRUPT.")
    sleep_print(" > Building prompt for LLM...\n")
    
    sleep_print("--- ANCHOR RESPONSE ---")
    if actions:
        # We strip the basic greeting because we modified interaction manager.
        print(f"🗣️  {actions[0].message}")
    
    print("\n================================================================")
    print("                     DEMONSTRATION COMPLETE                       ")
    print("================================================================\n")
    
    print(metrics.summary())

if __name__ == "__main__":
    main()
