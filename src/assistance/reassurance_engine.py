"""
MEMORA Patient Reassurance Engine.

Provides calm, consistent, non-contradictory responses for repeated questions, mild confusion,
and disorientation in Alzheimer's patients. Never shows impatience or contradicts past answers.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional, Tuple

from src.assistance.assistance_models import AssistanceOutcome


class ReassuranceEngine:
    """
    Thread-safe reassurance and repetition loop handler.
    """

    def __init__(self) -> None:
        self._question_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def handle_reassurance(
        self,
        patient_question: str,
        verified_answer: str,
        session_id: Optional[str] = None,
    ) -> AssistanceOutcome:
        """
        Evaluate patient question repetition and format a calm, gentle orientation cue.
        """
        q_norm = patient_question.strip().lower()
        actions: List[str] = ["Evaluated question repetition frequency"]

        with self._lock:
            # Count previous occurrences of this exact question
            repeat_count = sum(1 for entry in self._question_history if entry["question"] == q_norm)
            self._question_history.append({
                "question": q_norm,
                "session_id": session_id,
            })

            actions.append(f"Recorded question occurrence #{repeat_count + 1}")

            # Format gentle response based on repetition count
            if repeat_count == 0:
                summary = f"No problem at all! {verified_answer}"
            elif repeat_count < 3:
                summary = f"Just to remind you gently: {verified_answer}"
            else:
                summary = f"You are safe and everything is okay. {verified_answer} Would you like to relax together in the lounge?"
                actions.append("Triggered gentle redirection cue for high repetition frequency")

            return AssistanceOutcome(
                success=True,
                actions_executed=actions,
                escalation_required=repeat_count >= 5,  # Flag caregiver escalation if repeated >= 5 times
                caregiver_notification=f"Frequent repeated question detected ({repeat_count + 1} times): '{patient_question}'" if repeat_count >= 5 else None,
                confidence=1.0,
                summary=summary,
            )

    def get_repetition_count(self, question: str) -> int:
        q_norm = question.strip().lower()
        with self._lock:
            return sum(1 for entry in self._question_history if entry["question"] == q_norm)

    def clear(self) -> None:
        with self._lock:
            self._question_history.clear()
