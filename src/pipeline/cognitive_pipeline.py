"""
Samsung Anchor Cognitive Pipeline.

Executes one complete cognitive cycle.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import time

from src.cognition.memory_engine import MemoryEngine
from src.cognition.context_restoration_engine import ContextRestorationEngine
from src.cognition.context.registry import ContextProviderRegistry
from src.cognition.context.fusion_engine import ContextFusionEngine
from src.cognition.context.providers.identity import IdentityContextProvider
from src.cognition.context.providers.memory import MemoryContextProvider
from src.cognition.context.providers.temporal import TemporalContextProvider
from src.cognition.context.providers.continuity import ContinuityContextProvider
from src.cognition.context.providers.social import SocialContextProvider
from src.cognition.goals.inference_engine import GoalInferenceEngine

from src.interaction.actions import InteractionAction
from src.interaction.interaction_manager import InteractionManager
from src.core.metrics import metrics
from src.core.cognitive_stream import CognitiveStream
import traceback
from src.interaction.presence_engine import PresenceEngine

if TYPE_CHECKING:
    from src.memory.database import MemoraDatabase

class CognitivePipeline:

    def __init__(self, database: "MemoraDatabase") -> None:
        
        self.database = database
        self.presence_engine = PresenceEngine()

        # Inject the real SQLAlchemy-backed memory repository
        self.memory_repository = self.database.memory_repo

        self.memory_engine = MemoryEngine(
            self.memory_repository
        )
        
        # Setup Context Framework
        self.context_registry = ContextProviderRegistry()
        self.context_registry.register(IdentityContextProvider())
        self.context_registry.register(MemoryContextProvider(self.memory_engine))
        self.context_registry.register(TemporalContextProvider())
        self.context_registry.register(ContinuityContextProvider())
        self.context_registry.register(SocialContextProvider())
        
        self.context_fusion_engine = ContextFusionEngine(self.context_registry)

        self.goal_inference_engine = GoalInferenceEngine()

        self.context_restoration_engine = ContextRestorationEngine()

        self.interaction_manager = InteractionManager()

    def reset(self):
        self.presence_engine.reset()

    def process(
        self,
        recognition_result: dict,
    ) -> list[InteractionAction]:

        actions = []
        stream = CognitiveStream.instance()
        cycle_id = stream.next_cycle_id()
        cycle_start = time.perf_counter()
        
        try:
            metrics.start_timer("latency.cognition.total")
            
            # --------------------------------------------------
            # 1. Evaluate Presence
            # --------------------------------------------------
            
            event = self.presence_engine.process(recognition_result)
            
            if event is None:
                metrics.stop_timer("latency.cognition.total")
                return actions
                
            # --------------------------------------------------
            # 2. Collect Multimodal Context
            # --------------------------------------------------
            metrics.start_timer("latency.context.fusion")
            cognitive_context = self.context_fusion_engine.fuse_context(event)
            metrics.stop_timer("latency.context.fusion")
            
            # Optional Debugging output:
            mem_count = len(cognitive_context.memory.memories) if cognitive_context.memory else 0
            print(f"[DEBUG] Context Gathered. Memories: {mem_count}, Time: {cognitive_context.temporal.time_of_day if cognitive_context.temporal else 'Unknown'}")
            
            # --------------------------------------------------
            # 3. Goal Inference
            # --------------------------------------------------
            metrics.start_timer("latency.cognition.goal_inference")
            goal_hypotheses = self.goal_inference_engine.infer(cognitive_context)
            metrics.stop_timer("latency.cognition.goal_inference")
            
            # --------------------------------------------------
            # 4. Context Restoration & Attention
            # --------------------------------------------------
            metrics.start_timer("latency.cognition.attention_and_llm")
            recall = self.context_restoration_engine.generate_context_cue(
                cognitive_context=cognitive_context,
                goal_hypotheses=goal_hypotheses
            )
            metrics.stop_timer("latency.cognition.attention_and_llm")
            
            # --------------------------------------------------
            # 5. Interaction Manager
            # --------------------------------------------------
            action = self.interaction_manager.handle_event(
                event,
                recall,
            )
            
            if action is not None:
                actions.append(action)
                
            total_latency = time.perf_counter() - cycle_start
            metrics.stop_timer("latency.cognition.total")
            
            # --------------------------------------------------
            # 6. Emit to Experience Platform
            # --------------------------------------------------
            try:
                attention_decision = self.context_restoration_engine.attention_engine.evaluate(cognitive_context) if cognitive_context else None
                stream_event = CognitiveStream.build_event(
                    cycle_id=cycle_id,
                    cognitive_context=cognitive_context,
                    attention_decision=attention_decision,
                    goal_hypotheses=goal_hypotheses,
                    generated_response=recall.generated_response if recall else "",
                    final_action=actions[0].message if actions else "",
                    total_latency_ms=total_latency,
                )
                stream.emit(stream_event)
            except Exception:
                pass  # Never let stream emission crash the pipeline
            
        except Exception as e:
            print(f"[CognitivePipeline] FATAL ERROR: {e}")
            traceback.print_exc()
            # Graceful degradation: If anything fails, don't crash the background thread.
            # We can optionally issue a generic error interaction or just fail silently.
            pass

        return actions