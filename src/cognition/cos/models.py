"""
Cognitive Operating System — Data Models.

Defines the core value objects exchanged between COS components:
CognitiveAction, AttentionFocus, WorkingMemorySlot, CognitiveGraphEvent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any


class CognitiveActionType(str, Enum):
    """The category of action the COS recommends."""
    SPEAK = "SPEAK"
    RETRIEVE_MEMORY = "RETRIEVE_MEMORY"
    ASK_CLARIFICATION = "ASK_CLARIFICATION"
    REMAIN_SILENT = "REMAIN_SILENT"
    REDIRECT_ATTENTION = "REDIRECT_ATTENTION"
    ESCALATE_TO_CAREGIVER = "ESCALATE_TO_CAREGIVER"
    REQUEST_PERCEPTION = "REQUEST_PERCEPTION"


@dataclass
class CognitiveAction:
    """
    The output of the Decision Engine — a recommended action with reasoning trace.
    """
    action_type: CognitiveActionType
    reasoning_path: str
    confidence: float = 1.0
    suggested_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type.value,
            "reasoning_path": self.reasoning_path,
            "confidence": round(self.confidence, 3),
            "suggested_message": self.suggested_message,
            "metadata": self.metadata,
        }


class AttentionFocusState(str, Enum):
    """Lifecycle state of the current attention focus."""
    IDLE = "IDLE"
    ACQUIRED = "ACQUIRED"
    MAINTAINED = "MAINTAINED"
    INTERRUPTED = "INTERRUPTED"
    RELEASED = "RELEASED"


@dataclass
class AttentionFocus:
    """
    Represents the current cognitive attention target and its lifecycle state.
    """
    target: str = "None"
    state: AttentionFocusState = AttentionFocusState.IDLE
    acquired_at: float = 0.0
    cycle_count: int = 0
    priority_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        uptime = time.time() - self.acquired_at if self.acquired_at > 0 else 0.0
        return {
            "target": self.target,
            "state": self.state.value,
            "held_seconds": round(uptime, 2),
            "cycle_count": self.cycle_count,
            "priority_score": round(self.priority_score, 3),
        }


@dataclass
class WorkingMemorySlot:
    """
    A single slot in working memory with automatic TTL-based expiration.
    """
    key: str
    value: Any
    stored_at: float = field(default_factory=time.time)
    ttl_seconds: float = 300.0

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.stored_at) > self.ttl_seconds

    def to_dict(self) -> dict[str, Any]:
        remaining = max(0.0, self.ttl_seconds - (time.time() - self.stored_at))
        return {
            "key": self.key,
            "value": str(self.value),
            "remaining_ttl_seconds": round(remaining, 1),
            "is_expired": self.is_expired,
        }


@dataclass
class CognitiveGraphEvent:
    """
    A single node in the Cognitive Event Graph representing a causal cognitive event.
    """
    event_id: str
    event_type: str
    source: str
    target: str
    timestamp: float = field(default_factory=time.time)
    parent_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "target": self.target,
            "timestamp_iso": time.strftime("%H:%M:%S", time.localtime(self.timestamp)),
            "parent_id": self.parent_id,
            "metadata": self.metadata,
        }
