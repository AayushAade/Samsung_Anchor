"""
MEMORA Cognitive Reasoning Data Models.

Provides unified value objects for:
- Observation representation & taxonomy
- Temporal relations
- Hypotheses lifecycle & confidence
- Multi-modal conflict records
- Explainable reasoning graph nodes
- Estimated cognitive state modes
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ObservationCategory(str, Enum):
    VISION_FACE = "VISION_FACE"
    VISION_OBJECT = "VISION_OBJECT"
    WORKING_MEMORY = "WORKING_MEMORY"
    BEHAVIOUR_PREDICTION = "BEHAVIOUR_PREDICTION"
    ROUTINE_PATTERN = "ROUTINE_PATTERN"
    CONTEXT_SIGNAL = "CONTEXT_SIGNAL"
    GOAL_STATE = "GOAL_STATE"
    ATTENTION_FOCUS = "ATTENTION_FOCUS"
    SENSOR_HAL = "SENSOR_HAL"
    CLINICAL_STATE = "CLINICAL_STATE"


class TemporalRelation(str, Enum):
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    DURING = "DURING"
    RECENTLY = "RECENTLY"
    LONG_AGO = "LONG_AGO"
    STILL_OCCURRING = "STILL_OCCURRING"
    EXPIRED = "EXPIRED"


class HypothesisStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    CONFIRMED = "CONFIRMED"
    EXPIRED = "EXPIRED"


class CognitiveStateMode(str, Enum):
    SEARCHING = "SEARCHING"
    CONVERSING = "CONVERSING"
    IDLE = "IDLE"
    PREPARING_ACTIVITY = "PREPARING_ACTIVITY"
    FOLLOWING_ROUTINE = "FOLLOWING_ROUTINE"
    ROOM_TRANSITIONING = "ROOM_TRANSITIONING"
    WAITING = "WAITING"
    UNKNOWN = "UNKNOWN"


class ReasoningNodeType(str, Enum):
    CONCLUSION = "CONCLUSION"
    HYPOTHESIS = "HYPOTHESIS"
    EVIDENCE = "EVIDENCE"
    OBSERVATION = "OBSERVATION"


@dataclass
class Observation:
    """
    Unified Observation model standardising multi-modal sensory and cognitive evidence.
    """

    source: str
    category: ObservationCategory
    payload: Dict[str, Any]
    confidence: float = 1.0
    importance: float = 0.5
    expiry_seconds: float = 300.0
    provenance: str = "System"
    reasoning_tags: List[str] = field(default_factory=list)
    observation_id: str = field(default_factory=lambda: f"obs-{uuid.uuid4().hex[:8]}")
    timestamp_iso: str = field(default_factory=lambda: datetime.now().isoformat())
    created_ts: float = field(default_factory=time.time)

    def is_expired(self, current_ts: Optional[float] = None) -> bool:
        now = current_ts if current_ts is not None else time.time()
        return (now - self.created_ts) > self.expiry_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "source": self.source,
            "category": self.category.value,
            "confidence": round(self.confidence, 3),
            "importance": round(self.importance, 3),
            "expiry_seconds": self.expiry_seconds,
            "provenance": self.provenance,
            "reasoning_tags": list(self.reasoning_tags),
            "timestamp_iso": self.timestamp_iso,
            "payload": self.payload,
        }


@dataclass
class Hypothesis:
    """
    High-level cognitive hypothesis generated from multi-modal evidence.
    """

    title: str
    state_mode: CognitiveStateMode
    hypothesis_id: str = field(default_factory=lambda: f"hyp-{uuid.uuid4().hex[:8]}")
    confidence: float = 0.50
    supporting_observations: List[str] = field(default_factory=list)
    contradicting_observations: List[str] = field(default_factory=list)
    status: HypothesisStatus = HypothesisStatus.CANDIDATE
    created_at_iso: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated_iso: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "title": self.title,
            "state_mode": self.state_mode.value,
            "confidence": round(self.confidence, 3),
            "supporting_count": len(self.supporting_observations),
            "supporting_observations": list(self.supporting_observations),
            "contradicting_count": len(self.contradicting_observations),
            "contradicting_observations": list(self.contradicting_observations),
            "status": self.status.value,
            "created_at_iso": self.created_at_iso,
            "last_updated_iso": self.last_updated_iso,
        }


@dataclass
class ConflictRecord:
    """
    Record of detected multi-modal evidence contradictions.
    """

    title: str
    opposing_evidence_a: str
    opposing_evidence_b: str
    resolution_strategy: str
    resolved_winner: Optional[str] = None
    explanation: str = ""
    conflict_id: str = field(default_factory=lambda: f"cnf-{uuid.uuid4().hex[:8]}")
    timestamp_iso: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "title": self.title,
            "opposing_evidence_a": self.opposing_evidence_a,
            "opposing_evidence_b": self.opposing_evidence_b,
            "resolution_strategy": self.resolution_strategy,
            "resolved_winner": self.resolved_winner,
            "explanation": self.explanation,
            "timestamp_iso": self.timestamp_iso,
        }


@dataclass
class ReasoningGraphNode:
    """
    Node in the explainable reasoning graph tree.
    """

    node_type: ReasoningNodeType
    label: str
    node_id: str = field(default_factory=lambda: f"node-{uuid.uuid4().hex[:8]}")
    confidence: float = 1.0
    parent_ids: List[str] = field(default_factory=list)
    child_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "label": self.label,
            "confidence": round(self.confidence, 3),
            "parent_ids": list(self.parent_ids),
            "child_ids": list(self.child_ids),
        }
