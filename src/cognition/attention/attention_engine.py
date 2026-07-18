from typing import List
from src.cognition.memory_models import RelevantMemory
from src.cognition.context.models import CognitiveContext
from src.cognition.attention.attention_models import CognitiveState, AttentionDecision, ScoredMemory
from src.cognition.attention.scorers import (
    AttentionScorer, 
    BaseImportanceScorer, 
    RecencyScorer, 
    MedicalUrgencyScorer, 
    CommitmentScorer,
    AdaptiveAttentionScorer
)

class CognitiveAttentionEngine:
    """
    The Executive Function of Samsung Anchor.
    Determines WHICH memories deserve attention and WHETHER to interrupt the user.
    Replaces naive ranking.
    """
    
    # If the highest scored memory is below this threshold, the system remains silent.
    GLOBAL_ATTENTION_THRESHOLD = 35.0
    
    def __init__(self, max_attention_items: int = 3):
        self.max_attention_items = max_attention_items
        
        # Load the cognitive scoring modules
        self.scorers: List[AttentionScorer] = [
            BaseImportanceScorer(),
            RecencyScorer(),
            MedicalUrgencyScorer(),
            CommitmentScorer(),
            AdaptiveAttentionScorer()
        ]

    def evaluate(self, cognitive_context: CognitiveContext) -> AttentionDecision:
        """
        Calculates an attention score for every memory in the current context.
        If the highest score exceeds the threshold, returns an INTERRUPT decision.
        """
        
        memories = cognitive_context.memory.memories if cognitive_context.memory else []
        if not memories:
            return AttentionDecision(should_interrupt=False, selected_memories=[], highest_score=0.0)
            
        # Synthesize a CognitiveState for the scorers from the CognitiveContext
        
        state = CognitiveState(
            current_time=cognitive_context.temporal.current_time if cognitive_context.temporal else cognitive_context.timestamp,
            current_location="Living Room", # Mock for now until SpatialContext is added
            face_id=cognitive_context.identity.face_id if cognitive_context.identity else "unknown",
            name=cognitive_context.identity.name if cognitive_context.identity else None,
            relationship=cognitive_context.identity.relationship if cognitive_context.identity else None
        )
            
        scored_memories: List[ScoredMemory] = []
        
        # Compute combined attention score for each memory
        for memory in memories:
            total_score = 0.0
            for scorer in self.scorers:
                total_score += scorer.score(memory, state)
                
            scored_memories.append(ScoredMemory(memory=memory, attention_score=total_score))
            
        # Sort descending by attention score
        scored_memories.sort(key=lambda x: x.attention_score, reverse=True)
        
        # Determine Silence
        highest_score = scored_memories[0].attention_score
        if highest_score < self.GLOBAL_ATTENTION_THRESHOLD:
            # Silence: No memory reached the threshold to warrant interrupting the user
            print(f"[AttentionEngine] Highest score {highest_score:.1f} < Threshold {self.GLOBAL_ATTENTION_THRESHOLD}. Choosing SILENCE.")
            return AttentionDecision(should_interrupt=False, selected_memories=[])
            
        # Select top N memories that passed
        # We also might want to filter out memories below threshold even if highest passed, 
        # but for now, if we interrupt, we'll give the LLM the top few items to formulate context.
        selected = [sm.memory for sm in scored_memories[:self.max_attention_items]]
        
        print(f"[AttentionEngine] Highest score {highest_score:.1f} >= Threshold. Choosing INTERRUPT with {len(selected)} items.")
        return AttentionDecision(should_interrupt=True, selected_memories=selected)
