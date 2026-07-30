"""
MEMORA Interrupt Manager.

Handles external and internal interruptions safely:
- Emergency alerts
- Caregiver voice commands
- Urgent medication reminders
- Incoming conversation loops
- Sensor degradation events

Pauses active plan, records context, and enables safe resumption without duplicate work.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from src.executive.executive_models import InterruptEvent, InterruptType, Plan


class InterruptManager:
    """
    Manager for handling execution interruptions cleanly.
    """

    def __init__(self) -> None:
        self.active_interrupt: Optional[InterruptEvent] = None
        self.interrupted_plan_context: Optional[Plan] = None
        self._history: List[InterruptEvent] = []
        self._lock = threading.Lock()

    def handle_interrupt(
        self,
        interrupt_type: InterruptType,
        source: str,
        payload: Optional[Dict] = None,
        active_plan: Optional[Plan] = None,
    ) -> InterruptEvent:
        """
        Raise an interrupt signal, pausing the active plan and recording context.
        """
        event = InterruptEvent(
            interrupt_type=interrupt_type,
            source=source,
            payload=payload or {},
        )
        with self._lock:
            self.active_interrupt = event
            self.interrupted_plan_context = active_plan
            self._history.append(event)
            if len(self._history) > 30:
                self._history = self._history[-30:]
        return event

    def clear_interrupt(self) -> Optional[Plan]:
        """
        Clear active interrupt signal and return saved plan context for resumption.
        """
        with self._lock:
            saved_plan = self.interrupted_plan_context
            self.active_interrupt = None
            self.interrupted_plan_context = None
            return saved_plan

    def is_interrupted(self) -> bool:
        with self._lock:
            return self.active_interrupt is not None

    def get_interrupt_history(self) -> List[InterruptEvent]:
        with self._lock:
            return list(self._history)
