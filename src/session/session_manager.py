"""
MEMORA Session Manager.

CRUD lifecycle manager for CognitiveSession instances.
Creates sessions, transitions state deterministically, records execution traces,
and tracks participating subsystems. Performs no reasoning or planning.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.session.session_models import CognitiveSession, SessionState, SessionTransition
from src.session.session_context import SessionContext


class SessionManager:
    """
    Thread-safe lifecycle manager for cognitive sessions.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, CognitiveSession] = {}
        self._lock = threading.RLock()

    def create_session(
        self,
        patient_id: str = "default-patient",
        goal: str = "",
        priority: int = 1,
    ) -> CognitiveSession:
        session = CognitiveSession(
            patient_id=patient_id,
            goal=goal,
            priority=priority,
        )
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def transition(
        self,
        session_id: str,
        new_state: SessionState,
        reason: str = "",
    ) -> Optional[CognitiveSession]:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            transition = SessionTransition(
                from_state=session.current_state,
                to_state=new_state,
                reason=reason,
            )
            session.transitions.append(transition)
            session.current_state = new_state
            session.updated_at = datetime.now().isoformat()
            return session

    def record_subsystem(self, session_id: str, subsystem_name: str) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session and subsystem_name not in session.participating_subsystems:
                session.participating_subsystems.append(subsystem_name)

    def record_trace_step(
        self,
        session_id: str,
        subsystem: str,
        operation: str,
        duration_ms: float = 0.0,
        status: str = "OK",
    ) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.execution_trace.append({
                    "subsystem": subsystem,
                    "operation": operation,
                    "duration_ms": round(duration_ms, 3),
                    "status": status,
                    "timestamp_iso": datetime.now().isoformat(),
                })

    def complete_session(
        self,
        session_id: str,
        final_result: Dict[str, Any],
    ) -> Optional[CognitiveSession]:
        session = self.transition(session_id, SessionState.COMPLETED, reason="Pipeline execution finished")
        if session:
            with self._lock:
                session.final_result = final_result
        return session

    def fail_session(self, session_id: str, error: str) -> Optional[CognitiveSession]:
        session = self.transition(session_id, SessionState.FAILED, reason=error)
        if session:
            with self._lock:
                session.final_result = {"error": error}
        return session

    def get_session(self, session_id: str) -> Optional[CognitiveSession]:
        with self._lock:
            return self._sessions.get(session_id)

    def get_all_sessions(self) -> List[CognitiveSession]:
        with self._lock:
            return list(self._sessions.values())

    def get_session_count(self) -> int:
        with self._lock:
            return len(self._sessions)
