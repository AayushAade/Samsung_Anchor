"""
MEMORA Central Assistance Engine.

Public façade coordinating Context Restoration, Routine Guidance, Object Assistance,
Caregiver Assistance, and the Reassurance Engine into patient-centered workflows.
"""

from __future__ import annotations

import hashlib
import json
import threading
from typing import Any, Dict, List, Optional, Tuple

from src.assistance.assistance_models import (
    AssistanceOutcome,
    AssistancePlan,
    AssistancePriority,
    AssistanceScenario,
    AssistanceSnapshot,
)
from src.assistance.caregiver_assistance import CaregiverAssistanceWorkflow
from src.assistance.context_restoration import ContextRestorationWorkflow
from src.assistance.object_assistance import ObjectAssistanceWorkflow
from src.assistance.reassurance_engine import ReassuranceEngine
from src.assistance.routine_guidance import RoutineGuidanceWorkflow


class AssistanceEngine:
    """
    Unified public façade for Alzheimer's Cognitive Assistance.
    """

    def __init__(self) -> None:
        self.context_restoration = ContextRestorationWorkflow()
        self.routine_guidance = RoutineGuidanceWorkflow()
        self.object_assistance = ObjectAssistanceWorkflow()
        self.caregiver_assistance = CaregiverAssistanceWorkflow()
        self.reassurance_engine = ReassuranceEngine()

        self._active_plans: Dict[str, AssistancePlan] = {}
        self._executed_outcomes: List[Tuple[AssistancePlan, AssistanceOutcome]] = []
        self._lock = threading.RLock()

    def create_plan(
        self,
        scenario: AssistanceScenario,
        session_id: str,
        priority: AssistancePriority = AssistancePriority.NORMAL,
    ) -> AssistancePlan:
        plan = AssistancePlan(
            session_id=session_id,
            scenario=scenario,
            priority=priority,
            required_services=["MemoryEngine", "KnowledgeEngine", "ReasoningEngine", "ExecutiveEngine"],
            explanation_reference=f"Explanation for scenario {scenario.value}",
        )
        with self._lock:
            self._active_plans[plan.plan_id] = plan
            return plan

    def get_plan(self, plan_id: str) -> Optional[AssistancePlan]:
        with self._lock:
            return self._active_plans.get(plan_id)

    def execute(
        self,
        plan: AssistancePlan,
        context_data: Optional[Dict[str, Any]] = None,
        memory_engine: Optional[Any] = None,
        knowledge_engine: Optional[Any] = None,
    ) -> AssistanceOutcome:
        c_data = context_data or {}
        query = c_data.get("query", "")
        obj_name = c_data.get("object_name", "glasses")
        routine_name = c_data.get("routine_name", "MORNING")
        step_action = c_data.get("step_action", "NEXT")

        # Delegate execution based on scenario
        if plan.scenario == AssistanceScenario.CONTEXT_RESTORATION:
            outcome = self.context_restoration.restore_context(query, memory_engine, knowledge_engine)
        elif plan.scenario == AssistanceScenario.ROUTINE_GUIDANCE:
            outcome = self.routine_guidance.guide_routine(routine_name, step_action)
        elif plan.scenario == AssistanceScenario.OBJECT_RECALL:
            outcome = self.object_assistance.locate_object(obj_name, memory_engine, knowledge_engine)
        elif plan.scenario in (AssistanceScenario.REASSURANCE, AssistanceScenario.REPEATED_QUESTION):
            verified_ans = c_data.get("verified_answer", "You are safe at home with your family.")
            outcome = self.reassurance_engine.handle_reassurance(query, verified_ans, session_id=plan.session_id)
        else:
            outcome = AssistanceOutcome(
                success=True,
                actions_executed=["Executed default care workflow"],
                summary="Assistance provided.",
            )

        # Log intervention for caregiver tracking
        self.caregiver_assistance.log_intervention(
            scenario=plan.scenario.value,
            details=outcome.summary,
            escalation=outcome.escalation_required,
        )

        with self._lock:
            self._executed_outcomes.append((plan, outcome))
            return outcome

    def summarize_caregiver(self, patient_id: str = "default-patient") -> Dict[str, Any]:
        return self.caregiver_assistance.generate_caregiver_summary(patient_id)

    def explain(self, plan_id: str) -> str:
        """Return a human-readable explanation of an assistance plan and its execution status."""
        with self._lock:
            plan = self._active_plans.get(plan_id)
            if not plan:
                return f"Plan `{plan_id}` not found."

            outcome = next((o for p, o in self._executed_outcomes if p.plan_id == plan_id), None)
            out_str = f"Outcome: {outcome.summary}" if outcome else "Outcome: Pending Execution"

            return (
                f"Assistance Plan `{plan.plan_id}` [{plan.scenario.value}]\n"
                f"Session: `{plan.session_id}` | Priority: `{plan.priority.value}`\n"
                f"{out_str}"
            )

    def compute_checksum(self) -> str:
        with self._lock:
            data = {
                "plans": [p.plan_id for p in self._active_plans.values()],
                "outcomes": len(self._executed_outcomes),
            }
            raw = json.dumps(data, sort_keys=True).encode("utf-8")
            return hashlib.sha256(raw).hexdigest()[:16]

    def snapshot(self) -> AssistanceSnapshot:
        with self._lock:
            plans_cnt = len(self._active_plans)
            outcomes_cnt = len(self._executed_outcomes)
            escalations_cnt = sum(1 for _, o in self._executed_outcomes if o.escalation_required)
            chk = self.compute_checksum()

            return AssistanceSnapshot(
                active_plans_count=plans_cnt,
                executed_outcomes_count=outcomes_cnt,
                escalations_count=escalations_cnt,
                checksum=chk,
            )

    def reset(self) -> None:
        with self._lock:
            self._active_plans.clear()
            self._executed_outcomes.clear()
            self.context_restoration.clear()
            self.caregiver_assistance.clear()
            self.reassurance_engine.clear()
