from __future__ import annotations
from dataclasses import dataclass
from typing import List
from datetime import datetime
from src.cognition.memory_models import RelevantMemory

@dataclass(frozen=True)
class CognitiveState:
    """
    Represents the current environmental and internal state of the user.
    Used by the Attention Scorers to evaluate memory relevance.
    """
    current_time: datetime
    current_location: str
    face_id: str | None = None
    name: str | None = None
    relationship: str | None = None

@dataclass
class ScoredMemory:
    """
    A memory paired with its computed attention score.
    """
    memory: RelevantMemory
    attention_score: float

@dataclass(frozen=True)
class AttentionDecision:
    """
    The final output of the Cognitive Attention Engine.
    """
    should_interrupt: bool
    selected_memories: List[RelevantMemory]
    highest_score: float = 0.0
