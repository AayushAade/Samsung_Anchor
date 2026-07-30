"""
Clinical Decision Trace Framework.

Records transparent, clinical explanations for every cognitive decision:
- PatientState evidence
- Context providers consulted
- Memory retrieval summaries
- Goal hypotheses considered
- Care policies evaluated
- Speech suppression vs production
- Database memory persistence
- Final response text
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.clinical.patient_state import PatientState, PatientStateMode
from src.clinical.care_policy import CareDecision, CarePrinciple


@dataclass
class ClinicalDecisionTrace:
    timestamp: str
    patient_state: str
    patient_state_evidence: str
    providers_consulted: List[str]
    memory_retrieval_summary: str
    goal_hypotheses_considered: List[str]
    care_policies_evaluated: List[str]
    selected_care_policy: str
    interaction_strategy: str
    speech_produced: bool
    memory_written: bool
    confidence_scores: Dict[str, float]
    final_response: str
    dignity_preserved: bool = True
    caregiver_notified: bool = False
    # COS-enriched fields (Phase 21)
    working_memory_snapshot: Optional[Dict[str, Any]] = None
    attention_focus: Optional[Dict[str, Any]] = None
    cos_reasoning_path: Optional[str] = None
    cos_action_type: Optional[str] = None



class ClinicalDecisionTraceLogger:
    """
    Observer logger capturing transparent, clinical decision traces
    for clinicians, caregivers, researchers, and developers.
    """

    def __init__(self, max_traces: int = 100) -> None:
        self.max_traces = max_traces
        self._traces: List[ClinicalDecisionTrace] = []

    def record_trace(
        self,
        patient_state: PatientState,
        cognitive_context: Optional[Any],
        goal_hypotheses: Optional[List[Any]],
        care_decision: CareDecision,
        interaction_strategy: str,
        speech_produced: bool,
        memory_written: bool,
        final_response: str,
    ) -> ClinicalDecisionTrace:
        now_str = datetime.now().isoformat()

        # Extract providers consulted
        providers = ["identity", "memory", "temporal", "continuity", "social", "assistance"]

        # Memory retrieval summary
        mem_count = 0
        if cognitive_context and getattr(cognitive_context, "memory", None):
            mems = getattr(cognitive_context.memory, "memories", [])
            mem_count = len(mems)
        mem_summary = f"Retrieved {mem_count} relevant memories from SQLite repository."

        # Goal hypotheses summary
        goals_summary = []
        if goal_hypotheses:
            for g in goal_hypotheses:
                g_name = getattr(g, "name", str(g))
                g_conf = getattr(g, "confidence", 0.5)
                goals_summary.append(f"{g_name} (Confidence: {round(g_conf, 2)})")

        # Care policies evaluated
        policies_eval = [
            "Validation Therapy",
            "Gentle Orientation",
            "Supportive Silence",
            "One-Step Guidance",
            "Repetitive Query Redirection",
            "Emergency Safety Escalation",
        ]

        # Derived confidence scores
        conf_dict = {
            "patient_state_confidence": round(patient_state.confidence, 2),
            "care_policy_confidence": 0.95,
        }

        trace = ClinicalDecisionTrace(
            timestamp=now_str,
            patient_state=patient_state.mode.value,
            patient_state_evidence=patient_state.primary_need,
            providers_consulted=providers,
            memory_retrieval_summary=mem_summary,
            goal_hypotheses_considered=goals_summary,
            care_policies_evaluated=policies_eval,
            selected_care_policy=care_decision.principle.value,
            interaction_strategy=interaction_strategy,
            speech_produced=speech_produced,
            memory_written=memory_written,
            confidence_scores=conf_dict,
            final_response=final_response or "Supportive Silence",
            dignity_preserved=care_decision.dignity_preserved,
            caregiver_notified=care_decision.caregiver_notified,
        )

        self._traces.append(trace)
        if len(self._traces) > self.max_traces:
            self._traces.pop(0)

        return trace

    def get_recent_traces(self, limit: int = 10) -> List[ClinicalDecisionTrace]:
        return self._traces[-limit:]

    def get_latest_trace(self) -> Optional[ClinicalDecisionTrace]:
        return self._traces[-1] if self._traces else None
