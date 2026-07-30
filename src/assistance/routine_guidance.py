"""
MEMORA Routine Guidance Workflow.

Composes Executive Engine and Behaviour Platform to guide patients through daily routines
(morning, medication, meal, evening, sleep) in a step-by-step, interruptible manner.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from src.assistance.assistance_models import AssistanceOutcome


ROUTINE_STEPS: Dict[str, List[str]] = {
    "MORNING": [
        "Step 1: Good morning! Please drink a glass of water.",
        "Step 2: Time for breakfast in the kitchen.",
        "Step 3: Take your morning vitamin.",
    ],
    "MEDICATION": [
        "Step 1: Please locate your morning pill organizer on the kitchen counter.",
        "Step 2: Take the pill labeled 9:00 AM with water.",
        "Step 3: Place the organizer back on the counter.",
    ],
    "MEAL": [
        "Step 1: Wash hands at the sink.",
        "Step 2: Sit at the dining table for lunch.",
        "Step 3: Enjoy your lunch.",
    ],
    "EVENING": [
        "Step 1: Time for evening tea in the lounge.",
        "Step 2: Check that the front door is locked.",
        "Step 3: Relax and watch the evening news.",
    ],
    "SLEEP": [
        "Step 1: Put on pajamas.",
        "Step 2: Brush teeth in the bathroom.",
        "Step 3: Get into bed. Goodnight!",
    ],
}


class RoutineGuidanceWorkflow:
    """
    Thread-safe routine guidance orchestrator.
    """

    def __init__(self) -> None:
        self._current_step_index: Dict[str, int] = {}
        self._lock = threading.Lock()

    def guide_routine(
        self,
        routine_name: str = "MORNING",
        step_action: str = "NEXT",
    ) -> AssistanceOutcome:
        """
        Provide step-by-step guidance for a daily routine.
        """
        r_name = routine_name.upper()
        steps = ROUTINE_STEPS.get(r_name, ROUTINE_STEPS["MORNING"])

        with self._lock:
            curr_idx = self._current_step_index.get(r_name, 0)

            if step_action.upper() == "RESET":
                curr_idx = 0
            elif step_action.upper() == "NEXT":
                if curr_idx < len(steps) - 1:
                    curr_idx += 1
            elif step_action.upper() == "PREVIOUS":
                if curr_idx > 0:
                    curr_idx -= 1

            self._current_step_index[r_name] = curr_idx
            step_text = steps[curr_idx]

            actions = [
                f"Fetched routine `{r_name}`",
                f"Advanced to step index {curr_idx + 1} of {len(steps)}",
            ]

            return AssistanceOutcome(
                success=True,
                actions_executed=actions,
                escalation_required=False,
                summary=f"Routine [{r_name}]: {step_text}",
            )
