"""
MEMORA Caregiver Assistance Workflow.

Generates deterministic patient care summaries, intervention logs, escalation alerts,
and safety observations for family caregivers and clinical team members.
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.assistance.assistance_models import AssistanceOutcome


class CaregiverAssistanceWorkflow:
    """
    Thread-safe caregiver summary generator and safety observer.
    """

    def __init__(self) -> None:
        self._intervention_log: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def log_intervention(self, scenario: str, details: str, escalation: bool = False) -> None:
        with self._lock:
            self._intervention_log.append({
                "timestamp": datetime.now().isoformat(),
                "scenario": scenario,
                "details": details,
                "escalation": escalation,
            })

    def generate_caregiver_summary(
        self,
        patient_id: str = "default-patient",
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive, deterministic caregiver update payload.
        """
        with self._lock:
            total_interventions = len(self._intervention_log)
            escalations = [i for i in self._intervention_log if i.get("escalation")]

            summary_text = (
                f"Patient `{patient_id}` has received {total_interventions} cognitive assistance interactions. "
                f"{len(escalations)} intervention(s) required escalation attention."
            )

            return {
                "patient_id": patient_id,
                "timestamp": datetime.now().isoformat(),
                "total_interventions": total_interventions,
                "escalation_count": len(escalations),
                "interventions": list(self._intervention_log),
                "summary": summary_text,
                "recommended_action": "Check evening routine completion." if escalations else "Routine care progressing normally.",
            }

    def clear(self) -> None:
        with self._lock:
            self._intervention_log.clear()
