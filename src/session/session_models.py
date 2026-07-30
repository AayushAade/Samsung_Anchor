"""
MEMORA Cognitive Session Data Models.

Lightweight value objects representing one complete cognitive interaction episode.
"""

from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SessionState(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class SessionTransition:
    from_state: SessionState
    to_state: SessionState
    timestamp_iso: str = field(default_factory=lambda: datetime.now().isoformat())
    reason: str = ""


@dataclass
class CognitiveSession:
    """One complete cognitive interaction episode."""

    session_id: str = field(default_factory=lambda: f"ses-{uuid.uuid4().hex[:8]}")
    patient_id: str = "default-patient"
    goal: str = ""
    priority: int = 1
    current_state: SessionState = SessionState.CREATED
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    participating_subsystems: List[str] = field(default_factory=list)
    execution_trace: List[Dict[str, Any]] = field(default_factory=list)
    transitions: List[SessionTransition] = field(default_factory=list)
    context_reference: Optional[str] = None
    final_result: Optional[Dict[str, Any]] = None
    _start_ts: float = field(default_factory=time.time, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "patient_id": self.patient_id,
            "goal": self.goal,
            "priority": self.priority,
            "current_state": self.current_state.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "participating_subsystems": list(self.participating_subsystems),
            "execution_trace_steps": len(self.execution_trace),
            "transitions_count": len(self.transitions),
            "final_result": self.final_result,
        }
