"""
Samsung Anchor Cognitive Pipeline.

Executes one complete cognitive cycle.
"""

from __future__ import annotations

from src.cognition.memory_engine import MemoryEngine
from src.cognition.memory_query import MemoryQuery
from src.cognition.memory_repository import MemoryRepository
from src.cognition.reasoning_engine import ReasoningEngine

from src.interaction.actions import InteractionAction
from src.interaction.interaction_manager import InteractionManager
from src.interaction.presence_engine import PresenceEngine


class CognitivePipeline:

    def __init__(self) -> None:

        self.presence_engine = PresenceEngine()

        self.memory_repository = MemoryRepository()

        self.memory_engine = MemoryEngine(
            self.memory_repository
        )

        self.reasoning_engine = ReasoningEngine()

        self.interaction_manager = InteractionManager()

    def reset(self):

        self.presence_engine.reset()

    def process(
        self,
        recognition_result: dict,
    ) -> list[InteractionAction]:

        actions = []

        event = self.presence_engine.process(
            recognition_result
        )

        if event is None:
            return actions

        query = MemoryQuery(
            face_id=event.name
        )

        memories = self.memory_engine.retrieve(
            query
        )

        recall = self.reasoning_engine.recall(
            memories
        )

        action = self.interaction_manager.handle_event(
            event,
            recall,
        )

        if action is not None:
            actions.append(action)

        return actions