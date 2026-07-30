"""
Comprehensive test suite for the Cognitive Operating System (Phase 21).

Tests every COS component: models, working memory lifecycle, attention manager
focus transitions, decision engine multi-factor selection, event graph causal
chains, and the cognitive kernel end-to-end reasoning.
"""

import time
import pytest
from datetime import datetime

from src.cognition.cos.models import (
    CognitiveAction,
    CognitiveActionType,
    AttentionFocus,
    AttentionFocusState,
    WorkingMemorySlot,
    CognitiveGraphEvent,
)
from src.cognition.cos.working_memory import WorkingMemory
from src.cognition.cos.attention_manager import AttentionManager
from src.cognition.cos.decision_engine import DecisionEngine
from src.cognition.cos.event_graph import CognitiveEventGraph
from src.cognition.cos.kernel import CognitiveKernel
from src.cognition.attention.attention_models import AttentionDecision
from src.cognition.goals.models import GoalHypothesis, GoalCategory, GoalState
from src.clinical.patient_state import PatientState, PatientStateMode


# ======================================================================
# Stage 1: Data Models
# ======================================================================


class TestCOSModels:
    def test_cognitive_action_to_dict(self):
        action = CognitiveAction(
            action_type=CognitiveActionType.SPEAK,
            reasoning_path="P2: Goal active → SPEAK",
            confidence=0.85,
        )
        d = action.to_dict()
        assert d["action_type"] == "SPEAK"
        assert d["confidence"] == 0.85
        assert "P2" in d["reasoning_path"]

    def test_attention_focus_to_dict(self):
        focus = AttentionFocus(target="Locating Glasses", state=AttentionFocusState.ACQUIRED)
        d = focus.to_dict()
        assert d["target"] == "Locating Glasses"
        assert d["state"] == "ACQUIRED"

    def test_working_memory_slot_expiration(self):
        slot = WorkingMemorySlot(key="test", value="data", stored_at=time.time() - 400, ttl_seconds=300.0)
        assert slot.is_expired is True

        fresh_slot = WorkingMemorySlot(key="test", value="data", ttl_seconds=300.0)
        assert fresh_slot.is_expired is False

    def test_cognitive_graph_event_to_dict(self):
        ev = CognitiveGraphEvent(
            event_id="evt-abc123",
            event_type="VisitorRecognised",
            source="FaceRecognizer",
            target="IdentityRepo",
        )
        d = ev.to_dict()
        assert d["event_id"] == "evt-abc123"
        assert d["event_type"] == "VisitorRecognised"


# ======================================================================
# Stage 2: Working Memory
# ======================================================================


class TestWorkingMemory:
    def test_store_and_recall(self):
        wm = WorkingMemory()
        wm.store("current_visitor", {"name": "Riya"}, ttl_seconds=60.0)
        assert wm.recall("current_visitor") == {"name": "Riya"}

    def test_recall_missing_key(self):
        wm = WorkingMemory()
        assert wm.recall("nonexistent") is None

    def test_expire_stale(self):
        wm = WorkingMemory()
        wm.store("old_item", "stale_data", ttl_seconds=0.0)
        time.sleep(0.01)
        evicted = wm.expire_stale()
        assert evicted >= 1
        assert wm.recall("old_item") is None

    def test_snapshot(self):
        wm = WorkingMemory()
        wm.store("key_a", "value_a")
        snap = wm.snapshot()
        assert snap["slot_count"] >= 1
        assert "key_a" in snap["slots"]

    def test_capacity_enforcement(self):
        wm = WorkingMemory()
        for i in range(25):
            wm.store(f"slot_{i}", f"val_{i}")
        assert wm.active_slot_count <= WorkingMemory.MAX_SLOTS

    def test_clear(self):
        wm = WorkingMemory()
        wm.store("x", "y")
        wm.clear()
        assert wm.active_slot_count == 0


# ======================================================================
# Stage 3: Attention Manager
# ======================================================================


class TestAttentionManager:
    def _make_decision(self, should_interrupt: bool, score: float = 50.0):
        return AttentionDecision(should_interrupt=should_interrupt, selected_memories=[], highest_score=score)

    def test_idle_to_acquired(self):
        mgr = AttentionManager()
        focus = mgr.update_focus(self._make_decision(True), goals=None)
        assert focus.state == AttentionFocusState.ACQUIRED

    def test_acquired_to_maintained(self):
        mgr = AttentionManager()
        goal = GoalHypothesis(name="Find Glasses", category=GoalCategory.SEARCH, confidence=0.6, state=GoalState.ACTIVE)
        mgr.update_focus(self._make_decision(True), goals=[goal])
        focus = mgr.update_focus(self._make_decision(True), goals=[goal])
        assert focus.state == AttentionFocusState.MAINTAINED
        assert focus.cycle_count == 2

    def test_released_on_silence(self):
        mgr = AttentionManager()
        mgr.update_focus(self._make_decision(True), goals=None)
        focus = mgr.update_focus(self._make_decision(False), goals=None)
        assert focus.state == AttentionFocusState.RELEASED

    def test_interrupt_replaces_focus(self):
        mgr = AttentionManager()
        goal_a = GoalHypothesis(name="Task A", category=GoalCategory.DAILY_ROUTINE, confidence=0.5, state=GoalState.ACTIVE)
        goal_b = GoalHypothesis(name="Task B", category=GoalCategory.MEDICAL, confidence=0.8, state=GoalState.ACTIVE)
        mgr.update_focus(self._make_decision(True), goals=[goal_a])
        focus = mgr.update_focus(self._make_decision(True), goals=[goal_b])
        assert focus.target == "Task B"
        assert focus.cycle_count == 1


# ======================================================================
# Stage 4: Decision Engine
# ======================================================================


class TestDecisionEngine:
    def test_emergency_override(self):
        engine = DecisionEngine()
        ps = PatientState(mode=PatientStateMode.EMERGENCY, confidence=1.0, primary_need="Fall detected")
        action = engine.decide(context=None, goals=None, focus=AttentionFocus(), working_memory_snapshot={}, patient_state=ps)
        assert action.action_type == CognitiveActionType.ESCALATE_TO_CAREGIVER

    def test_active_goal_drives_action(self):
        engine = DecisionEngine()
        goal = GoalHypothesis(name="Medication Routine", category=GoalCategory.MEDICAL, confidence=0.6, state=GoalState.ACTIVE)
        ps = PatientState(mode=PatientStateMode.CALM, confidence=0.9, primary_need="Normal")
        action = engine.decide(context=None, goals=[goal], focus=AttentionFocus(), working_memory_snapshot={}, patient_state=ps)
        assert action.action_type == CognitiveActionType.SPEAK
        assert "P2" in action.reasoning_path

    def test_default_silence(self):
        engine = DecisionEngine()
        ps = PatientState(mode=PatientStateMode.CALM, confidence=0.9, primary_need="Normal")
        action = engine.decide(context=None, goals=None, focus=AttentionFocus(), working_memory_snapshot={}, patient_state=ps)
        assert action.action_type == CognitiveActionType.REMAIN_SILENT

    def test_anxious_patient_triggers_speak(self):
        engine = DecisionEngine()
        ps = PatientState(mode=PatientStateMode.ANXIOUS, confidence=0.9, primary_need="Reassurance")
        action = engine.decide(context=None, goals=None, focus=AttentionFocus(), working_memory_snapshot={}, patient_state=ps)
        assert action.action_type == CognitiveActionType.SPEAK
        assert "P5" in action.reasoning_path


# ======================================================================
# Stage 5: Cognitive Event Graph
# ======================================================================


class TestCognitiveEventGraph:
    def test_record_and_retrieve(self):
        graph = CognitiveEventGraph()
        eid = graph.record_event("TestEvent", "Source", "Target")
        assert eid.startswith("evt-")
        events = graph.get_recent_events(limit=5)
        assert len(events) == 1
        assert events[0].event_type == "TestEvent"

    def test_causal_chain(self):
        graph = CognitiveEventGraph()
        root = graph.record_event("Step1", "A", "B")
        child = graph.record_event("Step2", "B", "C", parent_id=root)
        grandchild = graph.record_event("Step3", "C", "D", parent_id=child)

        chain = graph.get_chain(root)
        assert len(chain) == 3
        assert chain[0].event_id == root
        assert chain[1].event_id == child
        assert chain[2].event_id == grandchild

    def test_session_graph(self):
        graph = CognitiveEventGraph()
        graph.record_event("E1", "S1", "T1")
        graph.record_event("E2", "S2", "T2")
        session = graph.get_session_graph()
        assert session["event_count"] == 2

    def test_capacity_limit(self):
        graph = CognitiveEventGraph()
        for i in range(600):
            graph.record_event(f"E{i}", "S", "T")
        session = graph.get_session_graph()
        assert session["event_count"] <= CognitiveEventGraph.MAX_EVENTS


# ======================================================================
# Stage 6: Cognitive Kernel
# ======================================================================


class TestCognitiveKernel:
    def test_kernel_reason_returns_action(self):
        kernel = CognitiveKernel()
        ps = PatientState(mode=PatientStateMode.CALM, confidence=0.9, primary_need="Normal routine")
        action = kernel.reason(context=None, goals=None, patient_state=ps, attention_decision=None)
        assert isinstance(action, CognitiveAction)
        assert action.action_type == CognitiveActionType.REMAIN_SILENT

    def test_kernel_populates_working_memory(self):
        kernel = CognitiveKernel()
        goal = GoalHypothesis(name="Morning Check", category=GoalCategory.DAILY_ROUTINE, confidence=0.5, state=GoalState.ACTIVE)
        ps = PatientState(mode=PatientStateMode.ORIENTED, confidence=0.8, primary_need="Daily routine")
        kernel.reason(context=None, goals=[goal], patient_state=ps, attention_decision=None)
        assert kernel.working_memory.recall("current_conversation") is not None
        assert kernel.working_memory.recall("patient_state") is not None

    def test_kernel_records_event_graph(self):
        kernel = CognitiveKernel()
        ps = PatientState(mode=PatientStateMode.CALM, confidence=0.9, primary_need="Normal")
        kernel.reason(context=None, goals=None, patient_state=ps, attention_decision=None)
        events = kernel.event_graph.get_recent_events(limit=10)
        assert len(events) >= 1
        assert events[0].event_type == "CognitiveKernel.reason"

    def test_kernel_state_summary(self):
        kernel = CognitiveKernel()
        ps = PatientState(mode=PatientStateMode.CALM, confidence=0.9, primary_need="Normal")
        kernel.reason(context=None, goals=None, patient_state=ps, attention_decision=None)
        summary = kernel.get_state_summary()
        assert summary["cycle_count"] == 1
        assert "working_memory" in summary
        assert "attention_focus" in summary

    def test_kernel_reset(self):
        kernel = CognitiveKernel()
        ps = PatientState(mode=PatientStateMode.CALM, confidence=0.9, primary_need="Normal")
        kernel.reason(context=None, goals=None, patient_state=ps, attention_decision=None)
        kernel.reset()
        assert kernel._cycle_count == 0
        assert kernel.working_memory.active_slot_count == 0

    def test_kernel_emergency_propagation(self):
        kernel = CognitiveKernel()
        ps = PatientState(mode=PatientStateMode.EMERGENCY, confidence=1.0, primary_need="Fall")
        action = kernel.reason(context=None, goals=None, patient_state=ps, attention_decision=None)
        assert action.action_type == CognitiveActionType.ESCALATE_TO_CAREGIVER
