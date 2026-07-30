from __future__ import annotations

from typing import List, Optional
from src.cognition.memory_models import RelevantMemory
from src.cognition.goals.models import GoalHypothesis
from src.interaction.events import PresenceEvent, PresenceEventType
from src.cognition.context_builder import ContextBuilder
from src.llm.reasoning_client import ReasoningClient, MockReasoningClient
from src.cognition.reasoning_models import MemoryRecall
from src.cognition.attention.attention_engine import CognitiveAttentionEngine
from src.cognition.context.models import CognitiveContext
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
        cognitive_context: CognitiveContext,
        goal_hypotheses: Optional[List[GoalHypothesis]] = None
    ) -> MemoryRecall:
        """
        Takes the unified CognitiveContext and GoalHypotheses,
        runs the Attention Engine, builds a goal-aware prompt,
        and gets a natural language response from the LLM.
        """
        
        # 1. Attention Engine (Executive Function)
        decision = self.attention_engine.evaluate(cognitive_context)
        
        if not decision.should_interrupt:
            # Cognitive Silence
            return MemoryRecall(
                should_greet=False,
                recalled_memories=[],
                generated_response=None
            )
            
        ranked_memories = decision.selected_memories
        
        # 2. Build Structured Context
        # Synthesize PresenceEvent for backwards compatibility with ContextBuilder
        synthesized_event = PresenceEvent(
            type=PresenceEventType.PERSON_ARRIVED,
            face_id=cognitive_context.identity.face_id if cognitive_context.identity else "unknown",
            name=cognitive_context.identity.name if cognitive_context.identity else None,
            relationship=cognitive_context.identity.relationship if cognitive_context.identity else None
        )
        
        prompt = self.builder.build_prompt(
            event=synthesized_event,
            memories=ranked_memories,
            current_location="Living Room", # Mock
            current_time=cognitive_context.temporal.time_of_day if cognitive_context.temporal else "Unknown",
            orientation=cognitive_context.continuity,
            social=cognitive_context.social,
            assistance=cognitive_context.assistance
        )
        
        # 2b. Inject Goal Awareness into the prompt
        if goal_hypotheses:
            top_goals = [g for g in goal_hypotheses if g.confidence > 0.10]
            if top_goals:
                goal_section = "\n\nInferred User Goals:\n"
                for g in top_goals[:3]:
                    goal_section += f"- {g.name} (Confidence: {g.confidence:.0%}, State: {g.state.value})\n"
                prompt += goal_section
        
        # 3. LLM Generation
        response_text = self.client.generate_cue(prompt)
        
        # We can still attach the memories used for context debugging/UI
        return MemoryRecall(
            should_greet=True,
            recalled_memories=ranked_memories,
            generated_response=response_text  # We will add this to MemoryRecall
        )
