"""
Cognitive Stream.

Emits structured JSON events from the Cognitive Pipeline
for consumption by the Experience Platform (dashboard, WebSocket, etc.).

This module mirrors CognitiveInspector but produces machine-readable
events instead of terminal output. It does NOT replace the Inspector —
both run in parallel.
"""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


@dataclass
class CognitiveEvent:
    """One complete snapshot of a cognitive pipeline cycle."""

    timestamp: str
    cycle_id: int

    # Identity
    face_id: Optional[str] = None
    name: Optional[str] = None
    relationship: Optional[str] = None
    identity_confidence: float = 0.0
    is_known: bool = False

    # Temporal
    time_of_day: Optional[str] = None
    day_of_week: Optional[str] = None

    # Daily Orientation & Continuity
    routine_stage: Optional[str] = None
    current_day: Optional[str] = None
    approximate_time: Optional[str] = None
    recent_activity: Optional[str] = None
    upcoming_activity: Optional[str] = None
    today_events: List[str] = None

    # Social & Relationship Context
    preferred_greeting: Optional[str] = None
    visit_frequency: Optional[str] = None
    last_interaction: Optional[str] = None
    shared_memories: List[Dict[str, Any]] = None
    important_dates: List[str] = None
    communication_preferences: Optional[str] = None
    care_notes: Optional[str] = None
    closeness_score: float = 0.0

    # Graduated Assistance Context
    assistance_level: int = 0
    assistance_level_name: Optional[str] = None
    assistance_level_label: Optional[str] = None
    assistance_rationale: Optional[str] = None
    escalation_triggered: bool = False

    # Conversation Engine Context
    conversation_state: Optional[str] = None
    active_speaker: Optional[str] = None
    response_strategy: Optional[str] = None
    interaction_type: Optional[str] = None
    turn_count: int = 0
    elapsed_seconds: float = 0.0
    conversation_topic: Optional[str] = None
    conversation_owner: Optional[str] = None

    # Clinical Ecosystem Context
    patient_name: Optional[str] = None
    primary_caregiver: Optional[str] = None
    pending_medications: List[str] = None
    upcoming_appointments: List[str] = None
    consent_granted: bool = True
    emergency_active: bool = False
    explanation_reason: Optional[str] = None

    # Edge Perception Context
    current_room: Optional[str] = None
    detected_activity: Optional[str] = None
    detected_objects: List[str] = None
    audio_events: List[str] = None
    sensor_fps: float = 30.0

    # Hardware Runtime Context
    runtime_mode: Optional[str] = None
    device_statuses: Dict[str, str] = None
    cpu_usage_pct: float = 0.0
    ram_usage_pct: float = 0.0
    connected_devices_count: int = 0

    # Operations & Observability Context
    deployment_profile: Optional[str] = None
    system_health_status: Optional[str] = None
    total_cycles_executed: int = 0
    active_errors_count: int = 0

    # Memory
    memories: List[Dict[str, Any]] = None
    memory_count: int = 0

    # Context Fusion
    providers_executed: int = 0
    provider_latencies: Dict[str, float] = None
    dropped_providers: List[str] = None

    # Goals
    goals: List[Dict[str, Any]] = None

    # Attention
    attention_decision: str = "SILENCE"
    attention_score: float = 0.0
    attention_threshold: float = 35.0
    selected_memory_count: int = 0

    # Interaction
    prompt_sent: Optional[str] = None
    generated_response: Optional[str] = None
    final_action: Optional[str] = None

    # Latencies
    total_latency_ms: float = 0.0

    def __post_init__(self):
        if self.memories is None:
            self.memories = []
        if self.provider_latencies is None:
            self.provider_latencies = {}
        if self.dropped_providers is None:
            self.dropped_providers = []
        if self.goals is None:
            self.goals = []
        if self.today_events is None:
            self.today_events = []
        if self.shared_memories is None:
            self.shared_memories = []
        if self.important_dates is None:
            self.important_dates = []

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)


class CognitiveStream:
    """
    Singleton stream that collects cognitive events and notifies subscribers.

    Usage::

        stream = CognitiveStream.instance()
        stream.subscribe(my_callback)
        stream.emit(event)
    """

    _instance: Optional["CognitiveStream"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._subscribers: List[Callable[[CognitiveEvent], None]] = []
        self._history: deque[CognitiveEvent] = deque(maxlen=100)
        self._cycle_counter = 0
        self._sub_lock = threading.Lock()

    @classmethod
    def instance(cls) -> "CognitiveStream":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def subscribe(self, callback: Callable[[CognitiveEvent], None]) -> None:
        with self._sub_lock:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[CognitiveEvent], None]) -> None:
        with self._sub_lock:
            self._subscribers = [s for s in self._subscribers if s is not callback]

    def get_history(self) -> List[CognitiveEvent]:
        return list(self._history)

    def next_cycle_id(self) -> int:
        self._cycle_counter += 1
        return self._cycle_counter

    def emit(self, event: CognitiveEvent) -> None:
        """Emit an event to all subscribers and store in history."""
        self._history.append(event)

        with self._sub_lock:
            subscribers = list(self._subscribers)

        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                print(f"[CognitiveStream] Subscriber error: {e}")

    @staticmethod
    def build_event(
        cycle_id: int,
        cognitive_context=None,
        attention_decision=None,
        goal_hypotheses=None,
        prompt: str = "",
        generated_response: str = "",
        final_action: str = "",
        total_latency_ms: float = 0.0,
        conversation_context=None,
        clinical_context=None,
        perception_context=None,
        runtime_summary=None,
        ops_summary=None,
    ) -> CognitiveEvent:
        """
        Build a CognitiveEvent from the raw pipeline outputs.
        Handles all the serialization so the pipeline doesn't have to.
        """

        event = CognitiveEvent(
            timestamp=datetime.now().isoformat(),
            cycle_id=cycle_id,
        )

        # Identity
        if cognitive_context and cognitive_context.identity:
            ident = cognitive_context.identity
            event.face_id = ident.face_id
            event.name = ident.name
            event.relationship = ident.relationship
            event.identity_confidence = ident.confidence
            event.is_known = ident.is_known

        # Temporal
        if cognitive_context and cognitive_context.temporal:
            event.time_of_day = cognitive_context.temporal.time_of_day
            event.day_of_week = cognitive_context.temporal.day_of_week

        # Daily Orientation & Continuity
        if cognitive_context and getattr(cognitive_context, "continuity", None):
            cont = cognitive_context.continuity
            event.routine_stage = getattr(cont, "routine_stage", None)
            event.current_day = getattr(cont, "current_day", None)
            event.approximate_time = getattr(cont, "approximate_time", None)
            event.recent_activity = getattr(cont, "recent_activity", None)
            event.upcoming_activity = getattr(cont, "upcoming_activity", None)
            event.today_events = list(getattr(cont, "today_events", []))

        # Social & Relationship Context
        if cognitive_context and getattr(cognitive_context, "social", None):
            soc = cognitive_context.social
            prof = getattr(soc, "active_profile", None)
            if prof:
                event.preferred_greeting = getattr(prof, "preferred_greeting", None)
                event.visit_frequency = getattr(prof, "visit_frequency", None)
                event.last_interaction = getattr(prof, "last_interaction", None)
                event.shared_memories = list(getattr(prof, "shared_memories", []))
                event.important_dates = list(getattr(prof, "important_dates", []))
                event.communication_preferences = getattr(prof, "communication_preferences", None)
                event.care_notes = getattr(prof, "care_notes", None)
                event.closeness_score = getattr(prof, "closeness_score", 0.95)

        # Graduated Assistance Context
        if cognitive_context and getattr(cognitive_context, "assistance", None):
            ast = cognitive_context.assistance
            event.assistance_level = getattr(ast, "level_code", 0)
            event.assistance_level_name = getattr(getattr(ast, "level", None), "name_simple", "Observe") if hasattr(getattr(ast, "level", None), "name_simple") else "Observe"
            event.assistance_level_label = getattr(ast, "level_label", "Level 0: Observe")
            event.assistance_rationale = getattr(ast, "rationale", None)
            event.escalation_triggered = getattr(ast, "escalation_triggered", False)

        # Conversation Engine Context
        if conversation_context:
            event.conversation_state = getattr(getattr(conversation_context, "state", None), "value", "Idle")
            event.active_speaker = getattr(getattr(conversation_context, "active_speaker", None), "value", "Patient")
            event.response_strategy = getattr(getattr(conversation_context, "response_strategy", None), "value", "Supportive Silence")
            event.interaction_type = getattr(getattr(conversation_context, "interaction_type", None), "value", "Casual")
            event.turn_count = getattr(conversation_context, "turn_count", 0)
            event.elapsed_seconds = getattr(conversation_context, "elapsed_seconds", 0.0)
            event.conversation_topic = getattr(conversation_context, "topic", "General Orientation & Support")
            event.conversation_owner = getattr(conversation_context, "owner", "Patient")

        # Clinical Ecosystem Context
        if clinical_context:
            event.patient_name = clinical_context.get("patient_name", "Eleanor")
            event.primary_caregiver = clinical_context.get("primary_caregiver", "Sarah Jenkins")
            event.pending_medications = clinical_context.get("pending_medications", [])
            event.upcoming_appointments = clinical_context.get("upcoming_appointments", [])
            event.consent_granted = clinical_context.get("consent_granted", True)
            event.emergency_active = clinical_context.get("emergency_active", False)
            event.explanation_reason = clinical_context.get("explanation_reason", None)

        # Edge Perception Context
        if perception_context:
            event.current_room = getattr(getattr(perception_context, "current_room", None), "value", "Living Room")
            event.detected_activity = getattr(getattr(perception_context, "detected_activity", None), "value", "Sitting")
            objs = getattr(perception_context, "detected_objects", [])
            event.detected_objects = [o.object_name if hasattr(o, "object_name") else str(o) for o in objs]
            auds = getattr(perception_context, "audio_events", [])
            event.audio_events = [a.event_type.value if hasattr(a, "event_type") and hasattr(a.event_type, "value") else str(a) for a in auds]
            event.sensor_fps = getattr(perception_context, "fps", 30.0)

        # Hardware Runtime Context
        if runtime_summary:
            event.runtime_mode = runtime_summary.get("mode", "Simulation Mode")
            event.device_statuses = runtime_summary.get("device_statuses", {})
            event.cpu_usage_pct = runtime_summary.get("cpu_usage_pct", 14.2)
            event.ram_usage_pct = runtime_summary.get("ram_usage_pct", 36.8)
            event.connected_devices_count = runtime_summary.get("connected_devices", 5)

        # Operations & Observability Context
        if ops_summary:
            event.deployment_profile = ops_summary.get("deployment_profile", "Simulation")
            event.system_health_status = ops_summary.get("system_health", "Healthy")
            event.total_cycles_executed = ops_summary.get("total_cycles", 0)
            event.active_errors_count = ops_summary.get("active_errors", 0)

        # Memory
        if cognitive_context and cognitive_context.memory:
            mems = cognitive_context.memory.memories or []
            event.memory_count = len(mems)
            event.memories = [
                {
                    "memory_id": m.memory_id,
                    "summary": m.summary,
                    "importance": m.importance.value if hasattr(m.importance, 'value') else m.importance,
                    "importance_label": m.importance.name if hasattr(m.importance, 'name') else str(m.importance),
                    "person": m.person,
                    "commitments": list(m.commitments) if m.commitments else [],
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                    "confidence": getattr(m, "confidence", 1.0),
                    "usefulness": getattr(m, "historical_usefulness", 0.5),
                }
                for m in mems
            ]

        # Context Fusion
        if cognitive_context:
            event.providers_executed = len(cognitive_context.provider_latencies)
            event.provider_latencies = dict(cognitive_context.provider_latencies)
            event.dropped_providers = list(cognitive_context.dropped_providers)

        # Goals
        if goal_hypotheses:
            event.goals = [
                {
                    "name": g.name,
                    "category": g.category.value if hasattr(g.category, 'value') else str(g.category),
                    "confidence": round(g.confidence, 4),
                    "state": g.state.value if hasattr(g.state, 'value') else str(g.state),
                    "supporting_evidence": [
                        {"source": e.source, "signal": e.signal, "weight": round(e.weight, 3)}
                        for e in (g.supporting_evidence or [])[-5:]
                    ],
                    "contradicting_evidence": [
                        {"source": e.source, "signal": e.signal, "weight": round(e.weight, 3)}
                        for e in (g.contradicting_evidence or [])[-3:]
                    ],
                }
                for g in goal_hypotheses
            ]

        # Attention
        if attention_decision:
            event.attention_decision = "INTERRUPT" if attention_decision.should_interrupt else "SILENCE"
            event.attention_score = getattr(attention_decision, "highest_score", 0.0)
            event.attention_threshold = 35.0
            event.selected_memory_count = len(attention_decision.selected_memories) if attention_decision.selected_memories else 0

        # Interaction
        event.prompt_sent = prompt if prompt else None
        event.generated_response = generated_response if generated_response else None
        event.final_action = final_action if final_action else None
        event.total_latency_ms = round(total_latency_ms * 1000, 2) if total_latency_ms else 0.0

        return event
