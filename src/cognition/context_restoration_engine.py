from __future__ import annotations

from typing import List
from src.cognition.memory_models import RelevantMemory
from src.interaction.events import PresenceEvent
from src.cognition.context_builder import ContextBuilder
from src.llm.reasoning_client import ReasoningClient, MockReasoningClient
from src.cognition.reasoning_models import MemoryRecall
from src.cognition.attention.attention_engine import CognitiveAttentionEngine
from src.cognition.attention.attention_models import CognitiveState
from datetime import datetime

class ContextRestorationEngine:
    """
    The true intelligence layer of Samsung Anchor.
    Bridges raw memory retrieval and LLM context generation.
    """
    
    def __init__(self, reasoning_client: ReasoningClient = None):
        self.attention_engine = CognitiveAttentionEngine(max_attention_items=3)
        self.builder = ContextBuilder()
        # Default to Mock client if none provided
        self.client = reasoning_client or MockReasoningClient()

    def generate_context_cue(
        self, 
        event: PresenceEvent, 
        raw_memories: List[RelevantMemory], 
        current_location: str, 
        current_time: str
    ) -> MemoryRecall:
        """
        Takes raw retrieved memories and an event, filters them, 
        builds a structured prompt, and gets a natural language response from the LLM.
        """
        
        # 1. Attention Engine (Executive Function)
        state = CognitiveState(
            current_time=datetime.now(),
            current_location=current_location,
            face_id=event.face_id,
            name=event.name,
            relationship=event.relationship
        )
        
        decision = self.attention_engine.evaluate(raw_memories, state)
        
        if not decision.should_interrupt:
            # Cognitive Silence
            return MemoryRecall(
                should_greet=False,
                recalled_memories=[],
                generated_response=None
            )
            
        ranked_memories = decision.selected_memories
        
        # 2. Build Structured Context
        prompt = self.builder.build_prompt(
            event=event,
            memories=ranked_memories,
            current_location=current_location,
            current_time=current_time
        )
        
        # 3. LLM Generation
        response_text = self.client.generate_cue(prompt)
        
        # We can still attach the memories used for context debugging/UI
        return MemoryRecall(
            should_greet=True,
            recalled_memories=ranked_memories,
            generated_response=response_text  # We will add this to MemoryRecall
        )
