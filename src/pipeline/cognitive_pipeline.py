"""
Samsung Anchor Cognitive Pipeline.

Executes one complete cognitive cycle.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from src.cognition.memory_engine import MemoryEngine
from src.cognition.memory_query import MemoryQuery
from src.cognition.context_restoration_engine import ContextRestorationEngine

from src.interaction.actions import InteractionAction
from src.interaction.interaction_manager import InteractionManager
from src.core.metrics import metrics
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

        self.context_restoration_engine = ContextRestorationEngine()

        self.interaction_manager = InteractionManager()

    def reset(self):
        self.presence_engine.reset()

    def process(
        self,
        recognition_result: dict,
    ) -> list[InteractionAction]:

        actions = []
        
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
            # 2. Retrieve Memory
            # --------------------------------------------------
            metrics.start_timer("latency.memory.retrieval")
            query = MemoryQuery(face_id=event.face_id)
            memories = self.memory_engine.retrieve(query)
            metrics.stop_timer("latency.memory.retrieval")
            
            print(f"[DEBUG] Memories retrieved: {len(memories)}")
            for m in memories:
                print(f"[DEBUG] Memory: {m.summary}, Importance: {m.importance}")
            
            # --------------------------------------------------
            # 3. Context Restoration & Attention
            # --------------------------------------------------
            metrics.start_timer("latency.cognition.attention_and_llm")
            # Use the new Context Restoration Engine to generate the rich LLM-backed recall
            # Passing mock location/time as we don't have dynamic env tracking perfectly wired yet
            recall = self.context_restoration_engine.generate_context_cue(
                event=event,
                raw_memories=memories,
                current_location="Living Room", 
                current_time="12:00 PM"
            )
            metrics.stop_timer("latency.cognition.attention_and_llm")
            
            # --------------------------------------------------
            # 4. Interaction Manager
            # --------------------------------------------------
            action = self.interaction_manager.handle_event(
                event,
                recall,
            )
            
            if action is not None:
                actions.append(action)
                
            metrics.stop_timer("latency.cognition.total")
            
        except Exception as e:
            print(f"[CognitivePipeline] FATAL ERROR: {e}")
            traceback.print_exc()
            # Graceful degradation: If anything fails, don't crash the background thread.
            # We can optionally issue a generic error interaction or just fail silently.
            pass

        return actions