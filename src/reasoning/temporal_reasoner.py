"""
MEMORA Temporal Reasoner.

Evaluates qualitative temporal relationships (BEFORE, AFTER, DURING, RECENTLY,
LONG_AGO, STILL_OCCURRING, EXPIRED) and constructs natural time narratives.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, Optional

from src.reasoning.reasoning_models import Observation, TemporalRelation


class TemporalReasoner:
    """
    Evaluates temporal intervals and relative relationships among observations.
    """

    @classmethod
    def evaluate_relation(
        cls, observation: Observation, current_ts: Optional[float] = None
    ) -> TemporalRelation:
        now = current_ts if current_ts is not None else time.time()
        age = now - observation.created_ts

        if age < 0:
            return TemporalRelation.DURING
        if age > observation.expiry_seconds:
            return TemporalRelation.EXPIRED
        if age <= 30.0:
            return TemporalRelation.STILL_OCCURRING
        if age <= 180.0:
            return TemporalRelation.RECENTLY
        if age <= 900.0:
            return TemporalRelation.BEFORE
        return TemporalRelation.LONG_AGO

    @classmethod
    def format_time_narrative(
        cls, subject: str, action_or_location: str, age_seconds: float
    ) -> str:
        """
        Generate human-readable temporal summary sentences.
        """
        if age_seconds < 60.0:
            secs = max(1, int(age_seconds))
            return f"{subject} was {action_or_location} {secs} seconds ago."
        mins = int(age_seconds / 60.0)
        if mins == 1:
            return f"{subject} was {action_or_location} 1 minute ago."
        if mins < 60:
            return f"{subject} was {action_or_location} {mins} minutes ago."
        hours = int(mins / 60.0)
        return f"{subject} was {action_or_location} {hours} hours ago."
