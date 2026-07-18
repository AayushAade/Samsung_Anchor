from concurrent.futures import ThreadPoolExecutor
from src.cognition.reflection.feedback import FeedbackEvent, FeedbackType
from src.cognition.reflection.confidence_manager import ConfidenceManager
from src.memory.models import InteractionRecordModel, SemanticNodeModel

class ReflectionEngine:
    """
    The Meta-Cognition Engine.
    Operates asynchronously to evaluate interactions and adapt memory confidence.
    """
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ReflectionEngine")
        
    def process_feedback(self, event: FeedbackEvent):
        """
        Ingest a feedback event and submit to the background queue.
        """
        self.executor.submit(self._reflect, event)
        
    def _reflect(self, event: FeedbackEvent):
        """
        The core reflection loop. Correlates feedback to past interactions
        and applies meta-cognitive updates.
        """
        try:
            with self.session_factory() as session:
                if not event.interaction_id:
                    print("[ReflectionEngine] Feedback lacks interaction_id. General adaptation not yet implemented.")
                    return
                    
                interaction = session.query(InteractionRecordModel).filter_by(id=event.interaction_id).first()
                if not interaction:
                    print(f"[ReflectionEngine] Interaction {event.interaction_id} not found.")
                    return
                    
                print(f"[ReflectionEngine] Processing {event.feedback_type} for Interaction {event.interaction_id}")
                
                # Apply feedback to all semantic nodes used in this interaction
                for memory_id in interaction.selected_memory_ids:
                    # We assume semantic memory IDs start with 'sem_' 
                    # If it's an episode, we skip for now since episodes are immutable past events
                    if str(memory_id).startswith("sem_"):
                        numeric_id = int(str(memory_id).replace("sem_", ""))
                        node = session.query(SemanticNodeModel).filter_by(id=numeric_id).first()
                        
                        if node:
                            if event.feedback_type == FeedbackType.CONFIRMATION:
                                ConfidenceManager.update_on_confirmation(node)
                            elif event.feedback_type == FeedbackType.CORRECTION:
                                ConfidenceManager.update_on_correction(node)
                            elif event.feedback_type == FeedbackType.IGNORED:
                                ConfidenceManager.update_on_ignored(node)
                                
                session.commit()
                print(f"[ReflectionEngine] Reflection complete. Confidence & Usefulness updated.")
        except Exception as e:
            print(f"[ReflectionEngine] Error during reflection: {e}")
