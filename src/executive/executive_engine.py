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
        self._lock = threading.RLock()

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
        cognitive_context: Optional[Any] = None,
        working_memory: Optional[Any] = None,
        patient_state: Optional[Any] = None,
        reasoning_summary: Optional[Dict[str, Any]] = None,
        behaviour_summary: Optional[Dict[str, Any]] = None,
        location: str = "Living Room",
        user_speech: Optional[str] = None,
        patient_state_mode: str = "Calm",
        emergency_active: bool = False,
        missed_medications: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute one cycle of full executive decision making (Phase 10).
        """
        start_ts = time.time()
        with self._lock:
            self._cycle_counter += 1

        from src.executive.situation_assessment import SituationAssessor
        from src.executive.risk_engine import ExecutiveRiskEngine
        from src.executive.executive_models import ExecutiveState, SelfReflection

        # 1. Situation Assessment -> World State
        situation = SituationAssessor.assess_situation(
            cognitive_context=cognitive_context,
            working_memory=working_memory,
            patient_state=patient_state,
            user_speech=user_speech,
            location=location,
        )

        # 2. Executive Risk Engine Evaluation
        risk_assessment = ExecutiveRiskEngine.evaluate_risk(
            situation=situation,
            emergency_active=emergency_active,
            missed_medications=missed_medications,
            user_speech=user_speech,
        )

        # 3. Check for Emergency Interrupt
        if emergency_active:
            self.interrupt_manager.handle_interrupt(
                interrupt_type=InterruptType.EMERGENCY_ALERT,
                source="EmergencyManager",
                payload={"mode": patient_state_mode},
            )

        # 4. Add dynamic goal if user utterance or reasoning indicates searching or medication
        if user_speech:
            u_lower = user_speech.lower()
            if any(kw in u_lower for kw in ("glasses", "keys", "wallet", "remote", "searching")):
                self.goal_manager.add_goal(
                    title="Locate Misplaced Object",
                    goal_type=GoalType.OPERATIONAL,
                    priority=0.85,
                    origin="Conversational Goal Engine",
                )
            elif any(kw in u_lower for kw in ("medicine", "pill", "medication")):
                self.goal_manager.add_goal(
                    title="Assist Medication Routine",
                    goal_type=GoalType.OPERATIONAL,
                    priority=0.90,
                    origin="Conversational Goal Engine",
                )

        # 5. Goal Arbitration -> Utility-Weighted Top Goal
        active_goals = self.goal_manager.get_active_goals()
        top_goal = self.priority_manager.arbitrate_goals(
            goals=active_goals,
            situation=situation,
            risk_assessment=risk_assessment,
        )

        # 6. Action Planning
        plan = self.planner.generate_plan(
            goal=top_goal,
            reasoning_summary=reasoning_summary,
            behaviour_summary=behaviour_summary,
        )
        is_valid, validation_errors = PlanValidator.validate_plan(plan)

        # 7. Execution Monitoring & State Evolution
        self.execution_monitor.set_active_plan(plan)
        has_divergence, divergence_reason = self.execution_monitor.check_divergence(
            current_location=location,
        )

        self.executive_state = ExecutiveState(
            emotion_estimate="Anxious" if situation.anxiety_level > 0.5 else "Calm",
            stress_level=situation.anxiety_level,
            confusion_score=situation.confusion_score,
            search_activity=situation.searching_activity,
            current_goal=top_goal.title,
            attention_target=situation.search_target or top_goal.title,
            risk_level=risk_assessment.level.value,
            current_room=location,
            visitor_present=situation.detected_people[0] if situation.detected_people else None,
            conversation_topic=situation.search_target or "General Orientation",
            care_strategy="Validation Therapy" if situation.anxiety_level > 0.5 else "Gentle Cueing",
            composite_confidence=plan.confidence,
        )

        # 8. Post-Response Self-Reflection Evaluation
        reflection = SelfReflection(
            was_successful=True,
            confidence_sufficient=plan.confidence >= 0.70,
            memory_updated=situation.searching_activity,
            goal_transition=top_goal.title,
            reflection_notes=f"Risk: {risk_assessment.level.value} ({risk_assessment.justification}). Goal: {top_goal.title}.",
        )

        explanation_narrative = PlanExplainer.generate_explanation(top_goal, plan)
        latency_ms = round((time.time() - start_ts) * 1000.0, 3)

        # 9. Format Developer Executive Trace (Objective 10)
        trace_output = (
            f"🧠 [EXECUTIVE TRACE Cycle #{self._cycle_counter}]\n"
            f"  • Situation       : Location={situation.current_location}, Patient={situation.patient_name}, Searching={situation.searching_activity} (Target: {situation.search_target})\n"
            f"  • Risk Level      : {risk_assessment.level.value} (Score: {risk_assessment.score:.2f}) — {risk_assessment.justification}\n"
            f"  • Goals Evaluated : {len(active_goals)} active goals\n"
            f"  • Chosen Goal     : '{top_goal.title}' (Utility: {top_goal.priority:.2f})\n"
            f"  • Care Strategy   : {self.executive_state.care_strategy}\n"
            f"  • Action Plan     : Plan ID {plan.plan_id[:8]} with {len(plan.tasks)} task steps (Confidence: {plan.confidence:.2f})\n"
            f"  • Self-Reflection : Success={reflection.was_successful}, ConfSufficient={reflection.confidence_sufficient}\n"
        )
        print(trace_output)

        return {
            "cycle": self._cycle_counter,
            "situation": situation.to_dict(),
            "risk_assessment": risk_assessment.to_dict(),
            "executive_state": self.executive_state.to_dict(),
            "active_goals_count": len(active_goals),
            "top_goal": top_goal.to_dict(),
            "active_plan": plan.to_dict(),
            "is_plan_validated": is_valid,
            "validation_errors": validation_errors,
            "is_interrupted": self.interrupt_manager.is_interrupted(),
            "has_divergence": has_divergence,
            "divergence_reason": divergence_reason,
            "self_reflection": reflection.to_dict(),
            "explanation_narrative": explanation_narrative,
            "planning_latency_ms": latency_ms,
        }

    def reset(self) -> None:
        with self._lock:
            self._cycle_counter = 0
            self.goal_manager._goals.clear()
            self.goal_manager._seed_baseline_goals()
            self.interrupt_manager.clear_interrupt()
