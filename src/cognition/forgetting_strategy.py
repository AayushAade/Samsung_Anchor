from datetime import datetime
from src.memory.models import SemanticNodeModel
from src.cognition.memory_taxonomy import MemoryImportance, MemoryCategory

class ForgettingStrategy:
    """
    Simulates the Lysosome / Decay process of the human brain.
    Facts that are not reinforced slowly decay in confidence.
    """
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def decay_memories(self, current_time: datetime = None):
        """
        Runs the decay algorithm across the entire Knowledge Graph.
        Called periodically (e.g., once a day).
        """
        now = current_time or datetime.now()
        
        with self.session_factory() as session:
            all_nodes = session.query(SemanticNodeModel).all()
            
            for node in all_nodes:
                # 1. Protection layer
                if node.importance >= MemoryImportance.CRITICAL.value:
                    continue # Never decay critical medical/safety info
                if node.category.lower() == MemoryCategory.RELATIONSHIP.value:
                    continue # Do not forget core relationships
                
                # 2. Calculate time since last reinforcement
                try:
                    last_reinforced = datetime.fromisoformat(node.last_reinforced)
                except Exception:
                    last_reinforced = now
                    
                days_old = (now - last_reinforced).total_seconds() / 86400.0
                
                # If less than a day has passed, don't decay yet
                if days_old < 1.0:
                    continue
                    
                # 3. Decay Curve (Importance buffers decay)
                # Low importance drops by 0.1 per day. High drops by 0.02.
                decay_rate = 0.1 / float(node.importance)
                
                node.confidence -= (decay_rate * days_old)
                
                # Reset reinforcement timestamp so we don't double-decay the same period
                node.last_reinforced = now.isoformat()
                
                # 4. Prune completely forgotten memories
                if node.confidence <= 0.1:
                    print(f"[ForgettingStrategy] Memory decayed completely: {node.subject} {node.predicate} {node.object_val}")
                    session.delete(node)
                    
            session.commit()
