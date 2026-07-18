"""
Samsung Anchor — Goal Reasoning Data Models.

Immutable representations of goal hypotheses, evidence signals,
and the enumerations that govern the goal lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List


class GoalState(Enum):
    """Lifecycle state of a goal hypothesis."""
    HYPOTHESIZED = "HYPOTHESIZED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"
    INTERRUPTED = "INTERRUPTED"


class GoalCategory(Enum):
    """Broad categories of user goals."""
    MEDICAL = "MEDICAL"
    DAILY_ROUTINE = "DAILY_ROUTINE"
    SOCIAL = "SOCIAL"
    SEARCH = "SEARCH"          # Looking for an object
    NAVIGATION = "NAVIGATION"  # Leaving / arriving
    LEISURE = "LEISURE"
    WORK = "WORK"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class EvidenceSignal:
    """
    One atomic piece of evidence supporting or contradicting a goal.
    Append-only — evidence is never deleted.
    """
    source: str          # e.g., "TemporalProvider", "MemoryProvider"
    signal: str          # e.g., "time_of_day=Morning"
    weight: float        # Contribution to confidence (positive = supporting)
    timestamp: datetime


@dataclass
class GoalHypothesis:
    """
    A single goal hypothesis with confidence, evidence, and lifecycle metadata.

    This is intentionally *mutable* so the GoalLifecycleManager can evolve
    it in-place within the GoalRepository.
    """
    name: str
    category: GoalCategory
    confidence: float

    state: GoalState = GoalState.HYPOTHESIZED

    supporting_evidence: List[EvidenceSignal] = field(default_factory=list)
    contradicting_evidence: List[EvidenceSignal] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    # How many consecutive cycles this goal has been below the abandonment threshold
    stale_cycles: int = 0

    # Constant thresholds (class-level defaults, overridable per-instance)
    ACTIVATION_THRESHOLD: float = 0.40
    ABANDONMENT_THRESHOLD: float = 0.10
    CONFIDENCE_CAP: float = 0.95
    DECAY_FACTOR: float = 0.95
    PRIOR_UNCERTAINTY: float = 1.0

    def recalculate_confidence(self) -> None:
        """
        Bayesian-like confidence from accumulated evidence.
        confidence = Σ(supporting) / (Σ(supporting) + Σ(contradicting) + prior)
        """
        sup = sum(e.weight for e in self.supporting_evidence)
        con = sum(e.weight for e in self.contradicting_evidence)
        denominator = sup + con + self.PRIOR_UNCERTAINTY

        if denominator == 0:
            self.confidence = 0.0
        else:
            self.confidence = min(self.CONFIDENCE_CAP, sup / denominator)

        self.last_updated = datetime.now()
