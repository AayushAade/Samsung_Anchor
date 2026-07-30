"""
MEMORA Associative Memory Engine.

Manages explainable associations between entities, locations, routines, and reminders:
e.g. Reading Glasses -> Margaret -> Bedroom -> Morning Routine -> Medication Reminder.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Set, Tuple


class AssociativeMemoryEngine:
    """
    Deterministic associative memory network.
    """

    def __init__(self) -> None:
        self._associations: Dict[str, Set[str]] = {}
        self._lock = threading.Lock()
        self._seed_baseline_associations()

    def add_association(self, concept_a: str, concept_b: str) -> None:
        ca = concept_a.lower()
        cb = concept_b.lower()
        with self._lock:
            self._associations.setdefault(ca, set()).add(cb)
            self._associations.setdefault(cb, set()).add(ca)

    def get_associated_concepts(self, concept: str) -> List[str]:
        c = concept.lower()
        with self._lock:
            return list(self._associations.get(c, set()))

    def _seed_baseline_associations(self) -> None:
        self.add_association("reading glasses", "margaret")
        self.add_association("reading glasses", "living room")
        self.add_association("donepezil medication", "margaret")
        self.add_association("donepezil medication", "morning routine")
