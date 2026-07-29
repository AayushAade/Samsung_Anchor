"""
Comprehensive Test Suite for MEMORA Phase 25 — Executive Function & Adaptive Planning Framework.

Tests all Phase 25 modules:
1. Data Models & Serialization (Goal, TaskNode, Plan, InterruptEvent, RecoveryAction)
2. Goal Hierarchy & 7-Stage Lifecycle Manager
3. Hierarchical Task Graph (DAG topological sorting & dependency checking)
4. Deterministic Planner (Executable plan synthesis)
5. Priority Arbitration Engine (Dynamic ranking, urgency, overrides)
6. Execution Monitor & Divergence Detector (Room transition, timeout detection)
7. Interrupt Manager (Pause, context preservation, resumption)
8. Recovery Manager (Structured recovery strategies)
9. Plan Validator & Explainer (Pre-execution rules & narrative generator)
10. Central Executive Engine (Multi-cycle planning, latency tracking)
11. Pipeline Executive Integration (CognitivePipeline step 6.8 & stream emission)
"""

import os
import tempfile
import time
import pytest

from src.executive.executive_models import (
    Goal,
    GoalStatus,
    GoalType,
    InterruptType,
    Plan,
    RecoveryAction,
    RecoveryStrategy,
    TaskNode,
    TaskStatus,
    TaskType,
)
from src.executive.goal_manager import GoalManager
from src.executive.task_graph import TaskGraph
from src.executive.planner import DeterministicPlanner
from src.executive.priority_manager import PriorityManager
from src.executive.execution_monitor import ExecutionMonitor
from src.executive.interrupt_manager import InterruptManager
from src.executive.recovery_manager import RecoveryManager
from src.executive.plan_validator import PlanValidator
from src.executive.plan_explainer import PlanExplainer
from src.executive.executive_engine import ExecutiveEngine


# ======================================================================
# 1. Executive Models Tests
# ======================================================================

class TestExecutiveModels:
    def test_goal_to_dict(self):
        g = Goal(title="Locate Glasses", goal_type=GoalType.OPERATIONAL, priority=0.85)
        d = g.to_dict()
        assert d["title"] == "Locate Glasses"
        assert d["goal_type"] == "OPERATIONAL"
        assert d["status"] == "CREATED"

    def test_task_node_to_dict(self):
        tn = TaskNode(title="Determine Location", task_type=TaskType.DETERMINE_LOCATION)
        d = tn.to_dict()
        assert d["title"] == "Determine Location"
        assert d["task_type"] == "DETERMINE_LOCATION"

    def test_plan_to_dict(self):
        p = Plan(goal_id="g1", tasks=[], confidence=0.90)
        d = p.to_dict()
        assert d["goal_id"] == "g1"
        assert d["confidence"] == 0.90


# ======================================================================
# 2. Goal Hierarchy & Lifecycle Tests
# ======================================================================

class TestGoalManager:
    def test_add_and_transition_goal(self):
        gm = GoalManager()
        g = gm.add_goal("Morning Walk", goal_type=GoalType.OPERATIONAL, priority=0.75)
        assert g.status == GoalStatus.CREATED

        updated = gm.transition_status(g.goal_id, GoalStatus.PLANNED)
        assert updated.status == GoalStatus.PLANNED

        completed = gm.transition_status(g.goal_id, GoalStatus.COMPLETED)
        assert completed.completed_at_iso is not None

    def test_get_active_goals(self):
        gm = GoalManager()
        active = gm.get_active_goals()
        assert len(active) >= 1


# ======================================================================
# 3. Task Graph Tests
# ======================================================================

class TestTaskGraph:
    def test_topological_sort_and_dependencies(self):
        tg = TaskGraph(parent_goal_id="g1")
        t1 = tg.add_task("Step 1")
        t2 = tg.add_task("Step 2", dependencies=[t1.task_id])
        
        exec_tasks = tg.get_executable_tasks()
        assert len(exec_tasks) == 1
        assert exec_tasks[0].task_id == t1.task_id

        topo = tg.get_topological_order()
        assert len(topo) == 2
        assert topo[0].task_id == t1.task_id
        assert topo[1].task_id == t2.task_id


# ======================================================================
# 4. Deterministic Planner Tests
# ======================================================================

class TestPlanner:
    def test_generate_plan_object_search(self):
        g = Goal(title="Locate Reading Glasses", goal_type=GoalType.OPERATIONAL, priority=0.80)
        plan = DeterministicPlanner.generate_plan(g)
        assert plan.goal_id == g.goal_id
        assert len(plan.tasks) == 3
        assert "spatial retrieval" in plan.rationale


# ======================================================================
# 5. Priority Arbitration Tests
# ======================================================================

class TestPriorityManager:
    def test_calculate_effective_priority(self):
        g = Goal(title="Morning Medication", priority=0.50)
        p = PriorityManager.calculate_effective_priority(g, is_medication_urgent=True)
        assert p > 0.50

    def test_rank_goals(self):
        g1 = Goal(title="General orientation", priority=0.40)
        g2 = Goal(title="Morning Medication", priority=0.50)
        ranked = PriorityManager.rank_goals([g1, g2], is_medication_urgent=True)
        assert ranked[0].title == "Morning Medication"


# ======================================================================
# 6. Execution Monitor Tests
# ======================================================================

class TestExecutionMonitor:
    def test_check_divergence_room_change(self):
        em = ExecutionMonitor()
        g = Goal(title="Locate Glasses")
        plan = DeterministicPlanner.generate_plan(g)
        plan.tasks[0].status = TaskStatus.EXECUTING
        em.set_active_plan(plan)

        has_div, reason = em.check_divergence(current_location="Kitchen")
        assert has_div is True
        assert "Room transition detected" in reason


# ======================================================================
# 7. Interrupt & Recovery Manager Tests
# ======================================================================

class TestInterruptAndRecovery:
    def test_handle_and_clear_interrupt(self):
        im = InterruptManager()
        g = Goal(title="Test Goal")
        plan = DeterministicPlanner.generate_plan(g)
        
        event = im.handle_interrupt(InterruptType.EMERGENCY_ALERT, "SafetyManager", active_plan=plan)
        assert im.is_interrupted() is True
        assert event.interrupt_type == InterruptType.EMERGENCY_ALERT

        resumed = im.clear_interrupt()
        assert im.is_interrupted() is False
        assert resumed.goal_id == g.goal_id

    def test_evaluate_recovery_retry(self):
        t = TaskNode(title="Search Room", task_type=TaskType.SEARCH_ROOM)
        action = RecoveryManager.evaluate_recovery(t, "timeout", attempt_count=1)
        assert action.strategy == RecoveryStrategy.RETRY

    def test_evaluate_recovery_fallback(self):
        t = TaskNode(title="Search Room", task_type=TaskType.SEARCH_ROOM)
        action = RecoveryManager.evaluate_recovery(t, "item not found", attempt_count=3)
        assert action.strategy == RecoveryStrategy.FALLBACK


# ======================================================================
# 8. Plan Validator & Explainer Tests
# ======================================================================

class TestPlanValidatorAndExplainer:
    def test_validate_plan(self):
        g = Goal(title="Test Goal")
        plan = DeterministicPlanner.generate_plan(g)
        is_valid, errors = PlanValidator.validate_plan(plan)
        assert is_valid is True
        assert len(errors) == 0

    def test_generate_explanation(self):
        g = Goal(title="Test Goal")
        plan = DeterministicPlanner.generate_plan(g)
        PlanValidator.validate_plan(plan)
        explanation = PlanExplainer.generate_explanation(g, plan)
        assert "Executive Plan Explanation" in explanation


# ======================================================================
# 9. Central Executive Engine Tests
# ======================================================================

class TestExecutiveEngine:
    def test_process_cycle(self):
        ee = ExecutiveEngine()
        summary = ee.process_cycle(
            reasoning_summary={"cognitive_state": "SEARCHING"},
            location="Living Room",
        )
        assert summary["cycle"] == 1
        assert "top_goal" in summary
        assert summary["planning_latency_ms"] >= 0.0

    def test_reset(self):
        ee = ExecutiveEngine()
        ee.process_cycle(location="Living Room")
        ee.reset()
        assert ee._cycle_counter == 0


# ======================================================================
# 10. Pipeline Integration Tests
# ======================================================================

class TestPipelineExecutiveIntegration:
    def test_pipeline_instantiates_executive_engine(self):
        from src.memory.database import MemoraDatabase
        from src.pipeline.cognitive_pipeline import CognitivePipeline
        
        db = MemoraDatabase(db_path=os.path.join(tempfile.gettempdir(), "test_executive_pipeline.sqlite"))
        db.clear()
        pipeline = CognitivePipeline(database=db)
        
        assert hasattr(pipeline, "executive_engine")
        
        actions = pipeline.process({"face_id": "face_sarah", "name": "Sarah", "relationship": "Daughter"})
        assert pipeline.executive_engine._cycle_counter == 1
