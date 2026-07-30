"""
Test Suite for MEMORA Phase 31 — Cognitive Session Framework.

Tests:
1. Session Models (creation, serialisation, state enum)
2. Session Context (reference container, no data ownership)
3. Session Manager (CRUD, lifecycle transitions, trace recording)
4. Session Explainer (Markdown summary generation)
5. Session Engine (pipeline wrapping, end-to-end integration)
6. Pipeline Integration (CognitivePipeline.session_engine attribute)
"""

import os
import tempfile
import pytest

from src.session.session_models import CognitiveSession, SessionState, SessionTransition
from src.session.session_context import SessionContext
from src.session.session_manager import SessionManager
from src.session.session_explainer import SessionExplainer
from src.session.session_engine import SessionEngine


# ======================================================================
# 1. Session Models
# ======================================================================

class TestSessionModels:
    def test_create_session(self):
        s = CognitiveSession(goal="Find glasses")
        assert s.current_state == SessionState.CREATED
        assert s.session_id.startswith("ses-")
        assert s.goal == "Find glasses"

    def test_session_to_dict(self):
        s = CognitiveSession(patient_id="margaret", goal="Medication reminder")
        d = s.to_dict()
        assert d["patient_id"] == "margaret"
        assert d["current_state"] == "CREATED"

    def test_session_states_enum(self):
        assert SessionState.RUNNING.value == "RUNNING"
        assert SessionState.COMPLETED.value == "COMPLETED"
        assert SessionState.FAILED.value == "FAILED"
        assert SessionState.CANCELLED.value == "CANCELLED"

    def test_session_transition_record(self):
        t = SessionTransition(
            from_state=SessionState.CREATED,
            to_state=SessionState.RUNNING,
            reason="Pipeline start",
        )
        assert t.from_state == SessionState.CREATED
        assert t.to_state == SessionState.RUNNING


# ======================================================================
# 2. Session Context
# ======================================================================

class TestSessionContext:
    def test_context_is_reference_only(self):
        ctx = SessionContext(
            executive_goal="Find glasses",
            knowledge_references=["ref-1", "ref-2"],
        )
        d = ctx.to_dict()
        assert d["executive_goal"] == "Find glasses"
        assert d["knowledge_references_count"] == 2
        # Context holds references, not the actual data
        assert "ref-1" not in str(d)

    def test_empty_context(self):
        ctx = SessionContext()
        d = ctx.to_dict()
        assert d["executive_goal"] is None
        assert d["memory_references_count"] == 0


# ======================================================================
# 3. Session Manager
# ======================================================================

class TestSessionManager:
    def test_create_and_retrieve(self):
        mgr = SessionManager()
        s = mgr.create_session(patient_id="margaret", goal="test")
        assert mgr.get_session(s.session_id) is s
        assert mgr.get_session_count() == 1

    def test_lifecycle_transitions(self):
        mgr = SessionManager()
        s = mgr.create_session()
        assert s.current_state == SessionState.CREATED

        mgr.transition(s.session_id, SessionState.RUNNING)
        assert s.current_state == SessionState.RUNNING
        assert len(s.transitions) == 1

        mgr.transition(s.session_id, SessionState.COMPLETED, reason="Done")
        assert s.current_state == SessionState.COMPLETED
        assert len(s.transitions) == 2

    def test_subsystem_recording(self):
        mgr = SessionManager()
        s = mgr.create_session()
        mgr.record_subsystem(s.session_id, "ReasoningEngine")
        mgr.record_subsystem(s.session_id, "ReasoningEngine")  # duplicate ignored
        assert s.participating_subsystems == ["ReasoningEngine"]

    def test_trace_step_recording(self):
        mgr = SessionManager()
        s = mgr.create_session()
        mgr.record_trace_step(s.session_id, "Vision", "detect", duration_ms=2.5)
        assert len(s.execution_trace) == 1
        assert s.execution_trace[0]["subsystem"] == "Vision"

    def test_complete_session(self):
        mgr = SessionManager()
        s = mgr.create_session()
        mgr.complete_session(s.session_id, {"action": "Greeting"})
        assert s.current_state == SessionState.COMPLETED
        assert s.final_result == {"action": "Greeting"}

    def test_fail_session(self):
        mgr = SessionManager()
        s = mgr.create_session()
        mgr.fail_session(s.session_id, "Test error")
        assert s.current_state == SessionState.FAILED
        assert s.final_result["error"] == "Test error"


# ======================================================================
# 4. Session Explainer
# ======================================================================

class TestSessionExplainer:
    def test_explain_completed_session(self):
        mgr = SessionManager()
        s = mgr.create_session(patient_id="margaret", goal="Find glasses")
        mgr.transition(s.session_id, SessionState.RUNNING)
        mgr.record_subsystem(s.session_id, "PerceptionManager")
        mgr.record_subsystem(s.session_id, "CognitiveReasoningEngine")
        mgr.record_trace_step(s.session_id, "PerceptionManager", "process_cycle", 1.2)
        mgr.complete_session(s.session_id, {"action": "Glasses on coffee table"})

        explanation = SessionExplainer.explain(s)
        assert "Cognitive Session Summary" in explanation
        assert "PerceptionManager" in explanation
        assert "Find glasses" in explanation
        assert "COMPLETED" in explanation

    def test_explain_failed_session(self):
        mgr = SessionManager()
        s = mgr.create_session()
        mgr.fail_session(s.session_id, "Sensor offline")
        explanation = SessionExplainer.explain(s)
        assert "Sensor offline" in explanation


# ======================================================================
# 5. Session Engine (Unit Tests)
# ======================================================================

class TestSessionEngine:
    def test_explain_latest_no_session(self):
        engine = SessionEngine()
        assert engine.explain_latest() == "No session has been executed yet."

    def test_session_manager_wired(self):
        engine = SessionEngine()
        assert engine.session_manager is not None
        assert engine.session_manager.get_session_count() == 0


# ======================================================================
# 6. Pipeline Integration
# ======================================================================

class TestPipelineSessionIntegration:
    def test_pipeline_has_session_engine(self):
        from src.memory.database import MemoraDatabase
        from src.pipeline.cognitive_pipeline import CognitivePipeline

        db = MemoraDatabase(db_path=os.path.join(tempfile.gettempdir(), "test_session_pipeline.sqlite"))
        db.clear()
        pipeline = CognitivePipeline(database=db)

        assert hasattr(pipeline, "session_engine")
        assert isinstance(pipeline.session_engine, SessionEngine)


