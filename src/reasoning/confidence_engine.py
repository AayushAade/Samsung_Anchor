"""
MEMORA Confidence Propagation Framework.

Implements probabilistic confidence propagation for hypothesis evaluation:
- Combines multi-modal evidence
- Rewards agreement among independent sources
- Penalizes contradictions
- Applies temporal decay smoothly
- Strictly bounds confidence in [0.0, 1.0] without confidence spikes
"""

from __future__ import annotations

import math
import time
from typing import List, Optional

from src.reasoning.reasoning_models import Observation


class ConfidenceEngine:
    """
    Probabilistic confidence propagation engine.
    """

    AGREEMENT_BOOST_FACTOR = 0.15
    CONTRADICTION_PENALTY_FACTOR = 0.20
    DEFAULT_HALF_LIFE_SEC = 300.0

    @classmethod
    def apply_agreement_reward(cls, current_confidence: float, obs_confidence: float) -> float:
        """
        Boost confidence when supporting evidence agrees.
        """
        current_confidence = max(0.0, min(1.0, current_confidence))
        obs_confidence = max(0.0, min(1.0, obs_confidence))
        delta = cls.AGREEMENT_BOOST_FACTOR * (1.0 - current_confidence) * obs_confidence
        return round(max(0.0, min(1.0, current_confidence + delta)), 4)

    @classmethod
    def apply_contradiction_penalty(cls, current_confidence: float, obs_confidence: float) -> float:
        """
        Reduce confidence when contradicting evidence is observed.
        """
        current_confidence = max(0.0, min(1.0, current_confidence))
        obs_confidence = max(0.0, min(1.0, obs_confidence))
        delta = cls.CONTRADICTION_PENALTY_FACTOR * current_confidence * obs_confidence
        return round(max(0.0, min(1.0, current_confidence - delta)), 4)

    @classmethod
    def apply_temporal_decay(
        cls, confidence: float, age_seconds: float, half_life_sec: float = 300.0
    ) -> float:
        """
        Decay confidence smoothly over time.
        """
        if age_seconds <= 0:
            return round(confidence, 4)
        decay_constant = math.log(2) / max(1.0, half_life_sec)
        factor = math.exp(-decay_constant * age_seconds)
        return round(max(0.0, min(1.0, confidence * factor)), 4)

    @classmethod
    def combine_evidence(
        cls,
        base_confidence: float,
        supporting: List[Observation],
        contradicting: List[Observation],
        current_ts: Optional[float] = None,
    ) -> float:
        """
        Synthesize overall confidence from supporting and contradicting observation sets.
        """
        now = current_ts if current_ts is not None else time.time()
        score = base_confidence

        for supp in supporting:
            score = cls.apply_agreement_reward(score, supp.confidence * supp.importance)
            age = max(0.0, now - supp.created_ts)
            score = cls.apply_temporal_decay(score, age, supp.expiry_seconds)

        for contra in contradicting:
            score = cls.apply_contradiction_penalty(score, contra.confidence * contra.importance)

        return round(max(0.05, min(0.95, score)), 4)
