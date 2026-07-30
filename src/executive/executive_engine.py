"""
MEMORA Central Executive Engine.

Orchestrates goal hierarchy management, deterministic planning, priority arbitration,
execution monitoring, interruption handling, recovery, plan validation, and explainability.

Positioned as the executive orchestration layer above Cognitive Reasoning (Phase 24)
and below Behaviour Intelligence (Phase 23).
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from src.core.interfaces import ICognitiveSubsystem
from src.executive.executive_models import Goal, GoalStatus, GoalType, InterruptType, Plan
from src.executive.goal_manager import GoalManager
from src.executive.planner import DeterministicPlanner
from src.executive.priority_manager import PriorityManager
from src.executive.execution_monitor import ExecutionMonitor
from src.executive.interrupt_manager import InterruptManager
from src.executive.recovery_manager import RecoveryManager
from src.executive.plan_validator import PlanValidator
from src.executive.plan_explainer import PlanExplainer


class ExecutiveEngine(ICognitiveSubsystem):
    """
    Central Executive Function Orchestrator.
    """

    def __init__(self) -> None:
        self.goal_manager = GoalManager()
        self.planner = DeterministicPlanner()
        self.priority_manager = PriorityManager()
        self.execution_monitor = ExecutionMonitor()
        self.interrupt_manager = InterruptManager()
        self.recovery_manager = RecoveryManager()
        self._cycle_counter = 0
        self._status = "INITIALIZED"
        self._lock = threading.Lock()

    def initialize(self) -> bool:
        with self._lock:
            self._status = "RUNNING"
            return True

    def shutdown(self) -> bool:
        with self._lock:
            self._status = "SHUTDOWN"
            return True

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.process_cycle(
            reasoning_summary=input_data.get("reasoning_summary"),
            behaviour_summary=input_data.get("behaviour_summary"),
            location=input_data.get("location", "Living Room"),
            user_speech=input_data.get("user_speech"),
            patient_state_mode=input_data.get("patient_state_mode", "Calm"),
            emergency_active=input_data.get("emergency_active", False),
        )

    def status(self) -> str:
        with self._lock:
            return self._status

    def health(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "status": self._status,
                "active_goals": len(self.goal_manager.get_active_goals()),
            }

    def metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {"cycle_count": self._cycle_counter}

    def explain(self) -> str:
        goals = self.goal_manager.get_active_goals()
        if goals:
            return f"Executive Engine: Active top goal is '{goals[0].title}' (Priority: {goals[0].priority:.2f})."
        return "Executive Engine: Monitoring default orientation goal."

    def process_cycle(
        self,
        reasoning_summary: Optional[Dict[str, Any]] = None,
        behaviour_summary: Optional[Dict[str, Any]] = None,
        location: str = "Living Room",
        user_speech: Optional[str] = None,
        patient_state_mode: str = "Calm",
        emergency_active: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute one cycle of executive planning and monitoring.

        Returns
        -------
        Dict[str, Any]
            Serialisable executive summary dictionary.
        """
        start_ts = time.time()
        with self._lock:
            self._cycle_counter += 1

        # 1. Check for Emergency Interrupt
        if emergency_active:
            self.interrupt_manager.handle_interrupt(
                interrupt_type=InterruptType.EMERGENCY_ALERT,
                source="EmergencyManager",
                payload={"mode": patient_state_mode},
            )

        # 2. Add dynamic goal if reasoning suggests searching or medication
        if reasoning_summary and reasoning_summary.get("cognitive_state") == "SEARCHING":
            self.goal_manager.add_goal(
                title="Locate Misplaced Object",
                goal_type=GoalType.OPERATIONAL,
                priority=0.85,
                origin="Cognitive Reasoning Engine",
            )

        # 3. Retrieve and rank active goals
        active_goals = self.goal_manager.get_active_goals()
        ranked_goals = self.priority_manager.rank_goals(
            active_goals,
            is_emergency=emergency_active,
        )

        top_goal = ranked_goals[0] if ranked_goals else Goal(title="Default Assistive Orientation")

        # 4. Generate & Validate Plan
        plan = self.planner.generate_plan(
            goal=top_goal,
            reasoning_summary=reasoning_summary,
            behaviour_summary=behaviour_summary,
        )
        is_valid, validation_errors = PlanValidator.validate_plan(plan)

        # 5. Monitor Execution & Divergence
        self.execution_monitor.set_active_plan(plan)
        has_divergence, divergence_reason = self.execution_monitor.check_divergence(
            current_location=location,
        )

        # 6. Build Explanation Narrative
        explanation_narrative = PlanExplainer.generate_explanation(top_goal, plan)

        latency_ms = round((time.time() - start_ts) * 1000.0, 3)

        return {
            "cycle": self._cycle_counter,
            "active_goals_count": len(active_goals),
            "top_goal": top_goal.to_dict(),
            "active_plan": plan.to_dict(),
            "is_plan_validated": is_valid,
            "validation_errors": validation_errors,
            "is_interrupted": self.interrupt_manager.is_interrupted(),
            "has_divergence": has_divergence,
            "divergence_reason": divergence_reason,
            "progress": self.execution_monitor.get_progress_summary(),
            "explanation_narrative": explanation_narrative,
            "planning_latency_ms": latency_ms,
        }

    def reset(self) -> None:
        with self._lock:
            self._cycle_counter = 0
            self.goal_manager._goals.clear()
            self.goal_manager._seed_baseline_goals()
            self.interrupt_manager.clear_interrupt()
