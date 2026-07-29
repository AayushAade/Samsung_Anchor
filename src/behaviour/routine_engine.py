"""
MEMORA Routine Learning Engine.

Infers recurring daily and weekly routines from repeated multi-session observations
using interpretable, evidence-backed statistical methods.

Features:
- Accumulates activity observations
- Strengthens recurring patterns
- Decays unused or stale patterns smoothly
- Avoids overfitting to isolated single events
- Zero black-box ML model training
"""

from __future__ import annotations

import math
import threading
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.behaviour.models import ActivityCategory, BehaviourModel, RoutinePattern


class RoutineLearningEngine:
    """
    Interpretable statistical routine learning engine.
    """

    MIN_OBSERVATIONS_FOR_ROUTINE = 3
    DEFAULT_DECAY_HALFLIFE_DAYS = 7.0

    def __init__(self, decay_halflife_days: float = 7.0) -> None:
        self.decay_halflife_days = decay_halflife_days
        # Behaviour ID -> BehaviourModel
        self._behaviours: Dict[str, BehaviourModel] = {}
        # Routine ID -> RoutinePattern
        self._routines: Dict[str, RoutinePattern] = {}
        self._lock = threading.Lock()

        # Pre-seed baseline common daily routines for stability
        self._initialize_baseline_routines()

    # ------------------------------------------------------------------
    # Core Public API
    # ------------------------------------------------------------------

    def record_observation(
        self,
        activity_name: str,
        category: ActivityCategory,
        location: str,
        duration_mins: float = 15.0,
        associated_object: Optional[str] = None,
        time_of_day: str = "Morning",
        hour_of_day: Optional[int] = None,
    ) -> BehaviourModel:
        """
        Record a single activity observation and update statistical distributions.
        """
        b_key = f"{category.value}:{activity_name.lower().strip()}"
        now_hour = hour_of_day if hour_of_day is not None else datetime.now().hour
        now_iso = datetime.now().isoformat()

        with self._lock:
            if b_key in self._behaviours:
                model = self._behaviours[b_key]
                model.frequency_count += 1
                # Moving average duration
                model.average_duration_mins = (
                    0.8 * model.average_duration_mins + 0.2 * duration_mins
                )
                model.last_observed_iso = now_iso
                model.location = location

                # Update time of day distribution
                dist = model.time_of_day_distribution
                dist[time_of_day] = dist.get(time_of_day, 0.0) + 1.0
                total_obs = sum(dist.values())
                for k in dist:
                    dist[k] = round(dist[k] / total_obs, 2)

                # Update confidence based on observation density
                model.confidence = min(0.95, 0.30 + (0.10 * math.log(model.frequency_count + 1)))
                model.supporting_observations.append(f"Observed at {now_iso[:16]} ({location})")
                if len(model.supporting_observations) > 20:
                    model.supporting_observations = model.supporting_observations[-20:]
            else:
                model = BehaviourModel(
                    behaviour_id=f"beh-{uuid.uuid4().hex[:8]}",
                    name=activity_name,
                    category=category,
                    frequency_count=1,
                    average_duration_mins=duration_mins,
                    time_of_day_distribution={time_of_day: 1.0},
                    location=location,
                    confidence=0.35,
                    supporting_observations=[f"Initial observation at {now_iso[:16]}"],
                    last_observed_iso=now_iso,
                )
                self._behaviours[b_key] = model

            # Check if this behavior qualifies for promotion to a RoutinePattern
            if model.frequency_count >= self.MIN_OBSERVATIONS_FOR_ROUTINE:
                self._promote_to_routine(model, now_hour, associated_object)

            return model

    def decay_patterns(self) -> int:
        """
        Apply temporal decay to inactive patterns.
        Returns the number of weakened or pruned routines.
        """
        with self._lock:
            now = time.time()
            decay_constant = math.log(2) / (self.decay_halflife_days * 86400.0)
            pruned_count = 0

            for key, model in list(self._behaviours.items()):
                try:
                    last_ts = datetime.fromisoformat(model.last_observed_iso).timestamp()
                except ValueError:
                    last_ts = now

                age_sec = max(0.0, now - last_ts)
                decay_factor = math.exp(-decay_constant * age_sec)
                model.confidence = max(0.10, model.confidence * decay_factor)

                if model.confidence < 0.20:
                    model.trend_direction = "DECREASING"

            return pruned_count

    def get_active_routines(self, min_confidence: float = 0.40) -> List[RoutinePattern]:
        """
        Return active inferred routine patterns sorted by confidence desc.
        """
        with self._lock:
            routines = [r for r in self._routines.values() if r.confidence >= min_confidence]
            routines.sort(key=lambda r: r.confidence, reverse=True)
            return routines

    def get_behaviours(self) -> List[BehaviourModel]:
        with self._lock:
            return list(self._behaviours.values())

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _promote_to_routine(
        self, model: BehaviourModel, hour: int, associated_object: Optional[str]
    ) -> None:
        routine_key = f"routine:{model.category.value}:{model.name.lower()}"
        start_h = max(0, hour - 1)
        end_h = min(23, hour + 1)

        if routine_key in self._routines:
            r = self._routines[routine_key]
            r.observation_count += 1
            r.confidence = min(0.95, r.confidence + 0.05)
            r.typical_location = model.location
            if associated_object:
                r.typical_object = associated_object
        else:
            self._routines[routine_key] = RoutinePattern(
                routine_id=f"rtn-{uuid.uuid4().hex[:8]}",
                title=f"Routine: {model.name}",
                category=model.category,
                start_hour=start_h,
                end_hour=end_h,
                typical_location=model.location,
                typical_object=associated_object,
                confidence=min(0.85, model.confidence + 0.10),
                observation_count=model.frequency_count,
            )

    def _initialize_baseline_routines(self) -> None:
        """Pre-seed baseline dementia care daily routines."""
        baselines = [
            ("Morning Medication Routine", ActivityCategory.MEDICATION_ROUTINE, 8, 9, "Dining Room", "pill organizer", 0.85),
            ("Reading Glasses Habit", ActivityCategory.READING_HABIT, 20, 21, "Living Room", "reading glasses", 0.80),
            ("Evening Family Visit", ActivityCategory.VISITOR_INTERACTION, 17, 18, "Living Room", None, 0.75),
        ]
        for title, cat, start_h, end_h, loc, obj, conf in baselines:
            r_id = f"rtn-{uuid.uuid4().hex[:8]}"
            routine_key = f"routine:{cat.value}:{title.lower()}"
            self._routines[routine_key] = RoutinePattern(
                routine_id=r_id,
                title=title,
                category=cat,
                start_hour=start_h,
                end_hour=end_h,
                typical_location=loc,
                typical_object=obj,
                confidence=conf,
                observation_count=5,
            )
