"""
MEMORA Shared Cognitive Blackboard Architecture.

Provides a thread-safe, decoupled reasoning workspace collecting multi-modal
observations from Vision, Behaviour, Working Memory, Attention, Goals, Safety,
Context Fusion, and Sensor HAL without modifying upstream modules.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from src.reasoning.reasoning_models import (
    ConflictRecord,
    Hypothesis,
    Observation,
    ObservationCategory,
)


class CognitiveBlackboard:
    """
    Shared cognitive workspace for storing and querying multi-modal evidence.
    """

    MAX_OBSERVATIONS = 300

    def __init__(self, max_observations: int = 300) -> None:
        self.max_observations = max_observations
        self._observations: Dict[str, Observation] = {}
        self._hypotheses: Dict[str, Hypothesis] = {}
        self._conflicts: List[ConflictRecord] = []
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Observation Methods
    # ------------------------------------------------------------------

    def post_observation(
        self,
        source: str,
        category: ObservationCategory,
        payload: Dict[str, Any],
        confidence: float = 1.0,
        importance: float = 0.5,
        expiry_seconds: float = 300.0,
        provenance: str = "System",
        reasoning_tags: Optional[List[str]] = None,
    ) -> Observation:
        """
        Post a new multi-modal observation to the blackboard workspace.
        """
        obs = Observation(
            source=source,
            category=category,
            payload=payload,
            confidence=max(0.0, min(1.0, confidence)),
            importance=max(0.0, min(1.0, importance)),
            expiry_seconds=expiry_seconds,
            provenance=provenance,
            reasoning_tags=reasoning_tags or [],
        )

        with self._lock:
            self._observations[obs.observation_id] = obs
            # Prune if bounds exceeded
            if len(self._observations) > self.max_observations:
                oldest_key = min(self._observations.keys(), key=lambda k: self._observations[k].created_ts)
                del self._observations[oldest_key]

        return obs

    def get_active_observations(
        self, category: Optional[ObservationCategory] = None
    ) -> List[Observation]:
        """
        Retrieve non-expired active observations, optionally filtered by category.
        """
        now = time.time()
        with self._lock:
            active = [obs for obs in self._observations.values() if not obs.is_expired(now)]
            if category:
                active = [obs for obs in active if obs.category == category]
            return active

    def prune_expired(self) -> int:
        """
        Remove expired observations from the workspace. Returns count purged.
        """
        now = time.time()
        with self._lock:
            expired_ids = [k for k, obs in self._observations.items() if obs.is_expired(now)]
            for eid in expired_ids:
                del self._observations[eid]
            return len(expired_ids)

    # ------------------------------------------------------------------
    # Hypothesis & Conflict Management
    # ------------------------------------------------------------------

    def set_hypotheses(self, hypotheses: List[Hypothesis]) -> None:
        with self._lock:
            self._hypotheses = {h.hypothesis_id: h for h in hypotheses}

    def get_hypotheses(self) -> List[Hypothesis]:
        with self._lock:
            return list(self._hypotheses.values())

    def record_conflict(self, conflict: ConflictRecord) -> None:
        with self._lock:
            self._conflicts.append(conflict)
            if len(self._conflicts) > 50:
                self._conflicts = self._conflicts[-50:]

    def get_conflicts(self) -> List[ConflictRecord]:
        with self._lock:
            return list(self._conflicts)

    def clear(self) -> None:
        with self._lock:
            self._observations.clear()
            self._hypotheses.clear()
            self._conflicts.clear()
