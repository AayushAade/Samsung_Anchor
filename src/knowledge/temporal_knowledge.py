"""
MEMORA Temporal Knowledge Manager.

Tracks evolving facts and entity location transitions over time while preserving historical context:
e.g., Reading Glasses located_in Bedroom (09:15) -> Kitchen (11:40) -> Living Room (14:20).
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class TemporalLocationTransition:
    entity_id: str
    entity_name: str
    from_room: str
    to_room: str
    timestamp_iso: str = field(default_factory=lambda: datetime.now().isoformat())


class TemporalKnowledgeManager:
    """
    Manages location transition timelines for entities over time.
    """

    def __init__(self) -> None:
        self._transitions: List[TemporalLocationTransition] = []
        self._lock = threading.Lock()
        self._seed_baseline_transitions()

    def record_transition(self, entity_id: str, entity_name: str, from_room: str, to_room: str) -> TemporalLocationTransition:
        t = TemporalLocationTransition(
            entity_id=entity_id,
            entity_name=entity_name,
            from_room=from_room,
            to_room=to_room,
        )
        with self._lock:
            self._transitions.append(t)
        return t

    def get_location_history(self, entity_id: str) -> List[TemporalLocationTransition]:
        with self._lock:
            return [t for t in self._transitions if t.entity_id == entity_id]

    def _seed_baseline_transitions(self) -> None:
        t1 = TemporalLocationTransition(entity_id="ent-glasses", entity_name="Reading Glasses", from_room="Bedroom", to_room="Living Room")
        self._transitions.append(t1)
