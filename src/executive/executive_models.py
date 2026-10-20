"""
MEMORA Executive Function Data Models.

Provides unified value objects for:
- Goal taxonomy, hierarchy, and 7-stage lifecycle
- Task nodes, dependencies, and task graphs
- Executable plans and plan validation status
- Interruption events and recovery strategies
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class GoalType(str, Enum):
    STRATEGIC = "STRATEGIC"
    OPERATIONAL = "OPERATIONAL"
    TASK = "TASK"
    ACTION = "ACTION"


class GoalStatus(str, Enum):
    CREATED = "CREATED"
    PLANNED = "PLANNED"
    EXECUTING = "EXECUTING"
    BLOCKED = "BLOCKED"
    INTERRUPTED = "INTERRUPTED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class TaskType(str, Enum):
    DETERMINE_LOCATION = "DETERMINE_LOCATION"
    SEARCH_ROOM = "SEARCH_ROOM"
    VERIFY_IDENTITY = "VERIFY_IDENTITY"
    SUGGEST_RETRIEVAL = "SUGGEST_RETRIEVAL"
    PROVIDE_ORIENTATION = "PROVIDE_ORIENTATION"
    CHECK_MEDICATION = "CHECK_MEDICATION"
    GENERAL_ACTION = "GENERAL_ACTION"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class InterruptType(str, Enum):
    EMERGENCY_ALERT = "EMERGENCY_ALERT"
    CAREGIVER_COMMAND = "CAREGIVER_COMMAND"
    MEDICATION_REMINDER = "MEDICATION_REMINDER"
    INCOMING_CONVERSATION = "INCOMING_CONVERSATION"
    SENSOR_DEGRADATION = "SENSOR_DEGRADATION"


class RecoveryStrategy(str, Enum):
    RETRY = "RETRY"
    FALLBACK = "FALLBACK"
    WAIT = "WAIT"
    REQUEST_EVIDENCE = "REQUEST_EVIDENCE"
    ESCALATE = "ESCALATE"
    TERMINATE = "TERMINATE"


@dataclass
class Goal:
    """
    Structured hierarchical goal with full 7-stage lifecycle tracking.
    """

    title: str
    goal_type: GoalType = GoalType.OPERATIONAL
    priority: float = 0.50
    status: GoalStatus = GoalStatus.CREATED
    dependencies: List[str] = field(default_factory=list)
    deadline_iso: Optional[str] = None
    estimated_effort_mins: float = 15.0
    confidence: float = 0.80
    origin: str = "System"
    goal_id: str = field(default_factory=lambda: f"goal-{uuid.uuid4().hex[:8]}")
    created_at_iso: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at_iso: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "title": self.title,
            "goal_type": self.goal_type.value,
            "priority": round(self.priority, 3),
            "status": self.status.value,
            "dependencies": list(self.dependencies),
            "deadline_iso": self.deadline_iso,
            "estimated_effort_mins": self.estimated_effort_mins,
            "confidence": round(self.confidence, 3),
            "origin": self.origin,
            "created_at_iso": self.created_at_iso,
            "completed_at_iso": self.completed_at_iso,
        }


@dataclass
class TaskNode:
    """
    Task graph node representing a discrete step in a plan.
    """

    title: str
    task_type: TaskType = TaskType.GENERAL_ACTION
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    parent_goal_id: Optional[str] = None
    estimated_duration_sec: float = 30.0
    action_payload: Dict[str, Any] = field(default_factory=dict)
    task_id: str = field(default_factory=lambda: f"task-{uuid.uuid4().hex[:8]}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "task_type": self.task_type.value,
            "status": self.status.value,
            "dependencies": list(self.dependencies),
            "parent_goal_id": self.parent_goal_id,
            "estimated_duration_sec": self.estimated_duration_sec,
            "action_payload": self.action_payload,
        }


@dataclass
class Plan:
    """
    Executable plan composed of an ordered task sequence.
    """

    goal_id: str
    tasks: List[TaskNode] = field(default_factory=list)
    confidence: float = 0.80
    rationale: str = ""
    is_validated: bool = False
    plan_id: str = field(default_factory=lambda: f"plan-{uuid.uuid4().hex[:8]}")
    created_at_iso: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal_id": self.goal_id,
            "tasks_count": len(self.tasks),
            "tasks": [t.to_dict() for t in self.tasks],
            "confidence": round(self.confidence, 3),
            "rationale": self.rationale,
            "is_validated": self.is_validated,
            "created_at_iso": self.created_at_iso,
        }


@dataclass
class InterruptEvent:
    """
    Event capturing external or internal interruption signals.
    """

    interrupt_type: InterruptType
    source: str
    payload: Dict[str, Any] = field(default_factory=dict)
    interrupt_id: str = field(default_factory=lambda: f"int-{uuid.uuid4().hex[:8]}")
    timestamp_iso: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interrupt_id": self.interrupt_id,
            "interrupt_type": self.interrupt_type.value,
            "source": self.source,
            "payload": self.payload,
            "timestamp_iso": self.timestamp_iso,
        }


@dataclass
class RecoveryAction:
    """
    Structured recovery decision for execution failures.
    """

    strategy: RecoveryStrategy
    target_task_id: str
    explanation: str
    action_id: str = field(default_factory=lambda: f"rec-{uuid.uuid4().hex[:8]}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "strategy": self.strategy.value,
            "target_task_id": self.target_task_id,
            "explanation": self.explanation,
        }


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class RiskAssessment:
    level: RiskLevel = RiskLevel.LOW
    score: float = 0.10
    factors: List[str] = field(default_factory=list)
    justification: str = "Baseline safe operating context."

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "score": round(self.score, 3),
            "factors": list(self.factors),
            "justification": self.justification,
        }


@dataclass
class Situation:
    patient_name: str = "Patient"
    time_of_day: str = "Day"
    current_location: str = "Living Room"
    detected_people: List[str] = field(default_factory=list)
    detected_objects: List[str] = field(default_factory=list)
    activity: str = "Sitting"
    is_night: bool = False
    repeating_question: bool = False
    question_count: int = 0
    searching_activity: bool = False
    search_target: Optional[str] = None
    pending_medication: bool = False
    confusion_score: float = 0.10
    anxiety_level: float = 0.10

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patient_name": self.patient_name,
            "time_of_day": self.time_of_day,
            "current_location": self.current_location,
            "detected_people": list(self.detected_people),
            "detected_objects": list(self.detected_objects),
            "activity": self.activity,
            "is_night": self.is_night,
            "repeating_question": self.repeating_question,
            "question_count": self.question_count,
            "searching_activity": self.searching_activity,
            "search_target": self.search_target,
            "pending_medication": self.pending_medication,
            "confusion_score": round(self.confusion_score, 2),
            "anxiety_level": round(self.anxiety_level, 2),
        }


@dataclass
class ExecutiveState:
    emotion_estimate: str = "Calm"
    stress_level: float = 0.10
    confusion_score: float = 0.10
    search_activity: bool = False
    current_goal: Optional[str] = None
    attention_target: Optional[str] = None
    risk_level: str = "LOW"
    current_room: str = "Living Room"
    visitor_present: Optional[str] = None
    conversation_topic: str = "General"
    care_strategy: str = "Minimal Intervention"
    composite_confidence: float = 0.90

    def to_dict(self) -> Dict[str, Any]:
        return {
            "emotion_estimate": self.emotion_estimate,
            "stress_level": round(self.stress_level, 2),
            "confusion_score": round(self.confusion_score, 2),
            "search_activity": self.search_activity,
            "current_goal": self.current_goal,
            "attention_target": self.attention_target,
            "risk_level": self.risk_level,
            "current_room": self.current_room,
            "visitor_present": self.visitor_present,
            "conversation_topic": self.conversation_topic,
            "care_strategy": self.care_strategy,
            "composite_confidence": round(self.composite_confidence, 2),
        }


@dataclass
class SelfReflection:
    was_successful: bool = True
    confidence_sufficient: bool = True
    memory_updated: bool = False
    goal_transition: Optional[str] = None
    reflection_notes: str = "Response delivered smoothly with high dignity."

    def to_dict(self) -> Dict[str, Any]:
        return {
            "was_successful": self.was_successful,
            "confidence_sufficient": self.confidence_sufficient,
            "memory_updated": self.memory_updated,
            "goal_transition": self.goal_transition,
            "reflection_notes": self.reflection_notes,
        }

