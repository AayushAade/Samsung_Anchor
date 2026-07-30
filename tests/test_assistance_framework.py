"""
Comprehensive Test Suite for MEMORA Phase 37 — Alzheimer's Cognitive Assistance Framework.

Tests:
1. Assistance Data Models (Serialization of AssistancePlan, AssistanceOutcome, AssistanceSnapshot)
2. Context Restoration Workflow ("Where am I?", "What am I doing?", "Who am I with?")
3. Routine Guidance Workflow (Step-by-step guidance for MORNING, MEDICATION, MEAL, SLEEP)
4. Object Assistance Workflow (Locating misplaced glasses, keys, wallet)
5. Caregiver Assistance Workflow (Logging interventions, generating caregiver summaries, escalations)
6. Reassurance Engine (Repeated question detection, gentle repetition, redirection cues)
7. Central Assistance Engine (Public façade create_plan, execute, summarize_caregiver, snapshot, explain)
8. Assistance Explainer (Deterministic Markdown diagnostic report generation)
"""

import pytest
from src.assistance import (
    VERIFIED_OBJECT_LOCATIONS,
    AssistanceEngine,
    AssistanceExplainer,
    AssistanceOutcome,
    AssistancePlan,
    AssistancePriority,
    AssistanceScenario,
    AssistanceSnapshot,
    CaregiverAssistanceWorkflow,
    ContextRestorationWorkflow,
    ObjectAssistanceWorkflow,
    ReassuranceEngine,
    RoutineGuidanceWorkflow,
)


# ======================================================================
# 1. Assistance Data Models Tests
# ======================================================================

class TestAssistanceModels:
    def test_plan_serialization(self):
        plan = AssistancePlan(
            session_id="ses-100",
            scenario=AssistanceScenario.CONTEXT_RESTORATION,
            priority=AssistancePriority.HIGH,
        )
        d = plan.to_dict()
        assert d["session_id"] == "ses-100"
        assert d["scenario"] == "CONTEXT_RESTORATION"
        assert d["priority"] == "HIGH"
        assert plan.is_high_priority() is True

    def test_outcome_serialization(self):
        out = AssistanceOutcome(
            success=True,
            actions_executed=["Action 1"],
            summary="Context restored.",
        )
        d = out.to_dict()
        assert d["success"] is True
        assert "Action 1" in d["actions_executed"]

    def test_snapshot_serialization(self):
        snap = AssistanceSnapshot(
            active_plans_count=3,
            executed_outcomes_count=5,
            escalations_count=1,
            checksum="abc12345",
        )
        assert snap.to_dict()["active_plans_count"] == 3


# ======================================================================
# 2. Context Restoration Workflow Tests
# ======================================================================

class TestContextRestorationWorkflow:
    def test_restore_location_context(self):
        wf = ContextRestorationWorkflow()
        outcome = wf.restore_context("Where am I?")
        assert outcome.success is True
        assert "living room" in outcome.summary.lower()

    def test_restore_activity_context(self):
        wf = ContextRestorationWorkflow()
        outcome = wf.restore_context("What am I doing?")
        assert outcome.success is True
        assert len(outcome.actions_executed) > 0

    def test_restore_person_context(self):
        wf = ContextRestorationWorkflow()
        outcome = wf.restore_context("Who is this with me?")
        assert outcome.success is True
        assert "Sarah" in outcome.summary or "with" in outcome.summary


# ======================================================================
# 3. Routine Guidance Workflow Tests
# ======================================================================

class TestRoutineGuidanceWorkflow:
    def test_guide_morning_routine(self):
        wf = RoutineGuidanceWorkflow()
        o1 = wf.guide_routine("MORNING", "RESET")
        assert "Step 1" in o1.summary

        o2 = wf.guide_routine("MORNING", "NEXT")
        assert "Step 2" in o2.summary


# ======================================================================
# 4. Object Assistance Workflow Tests
# ======================================================================

class TestObjectAssistanceWorkflow:
    def test_locate_glasses(self):
        wf = ObjectAssistanceWorkflow()
        outcome = wf.locate_object("glasses")
        assert outcome.success is True
        assert "living room" in outcome.summary.lower()

    def test_locate_unknown_object(self):
        wf = ObjectAssistanceWorkflow()
        outcome = wf.locate_object("unknown_telescope")
        assert outcome.success is False
        assert "do not have a recent verified observation" in outcome.summary


# ======================================================================
# 5. Caregiver Assistance Workflow Tests
# ======================================================================

class TestCaregiverAssistanceWorkflow:
    def test_caregiver_summary_generation(self):
        wf = CaregiverAssistanceWorkflow()
        wf.log_intervention("CONTEXT_RESTORATION", "Answered location query", escalation=False)
        wf.log_intervention("REPEATED_QUESTION", "Repeated question loop", escalation=True)

        summary = wf.generate_caregiver_summary("pat-margaret")
        assert summary["patient_id"] == "pat-margaret"
        assert summary["total_interventions"] == 2
        assert summary["escalation_count"] == 1


# ======================================================================
# 6. Reassurance Engine Tests
# ======================================================================

class TestReassuranceEngine:
    def test_handle_reassurance(self):
        engine = ReassuranceEngine()
        q = "What day is it today?"
        ans = "Today is Thursday, July 30th."

        # First time
        o1 = engine.handle_reassurance(q, ans)
        assert o1.success is True
        assert ans in o1.summary

        # Multiple repetitions trigger gentle redirection
        for _ in range(3):
            engine.handle_reassurance(q, ans)

        o_repeat = engine.handle_reassurance(q, ans)
        assert "safe" in o_repeat.summary.lower() or "gently" in o_repeat.summary.lower()


# ======================================================================
# 7. Central Assistance Engine Tests
# ======================================================================

class TestAssistanceEngine:
    def test_engine_plan_create_and_execute(self):
        engine = AssistanceEngine()
        plan = engine.create_plan(AssistanceScenario.CONTEXT_RESTORATION, session_id="ses-engine-101")
        assert plan.scenario == AssistanceScenario.CONTEXT_RESTORATION

        outcome = engine.execute(plan, context_data={"query": "Where am I?"})
        assert outcome.success is True

        snap = engine.snapshot()
        assert snap.active_plans_count == 1
        assert snap.executed_outcomes_count == 1

        exp_str = engine.explain(plan.plan_id)
        assert plan.plan_id in exp_str

    def test_engine_caregiver_summary(self):
        engine = AssistanceEngine()
        plan = engine.create_plan(AssistanceScenario.ROUTINE_GUIDANCE, session_id="ses-102")
        engine.execute(plan, context_data={"routine_name": "MORNING"})

        summary = engine.summarize_caregiver("margaret")
        assert summary["total_interventions"] >= 1


# ======================================================================
# 8. Assistance Explainer Tests
# ======================================================================

class TestAssistanceExplainer:
    def test_explain_engine_state(self):
        engine = AssistanceEngine()
        plan = engine.create_plan(AssistanceScenario.OBJECT_RECALL, session_id="ses-103")
        engine.execute(plan, context_data={"object_name": "glasses"})

        markdown = AssistanceExplainer.explain_engine_state(engine)
        assert "MEMORA Alzheimer's Cognitive Assistance Diagnostic Report" in markdown
        assert "Caregiver Summary" in markdown
        assert "Executed Outcome History" in markdown
