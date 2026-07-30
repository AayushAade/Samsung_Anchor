"""
MEMORA Hypothesis Manager & Cognitive State Estimator.

Generates, updates, and evaluates high-level cognitive hypotheses:
- User searching for misplaced object
- User preparing activity or transitioning rooms
- User following daily routine
- User engaged in social conversation

Estimates current high-level CognitiveStateMode with transparent evidence links.
"""

from __future__ import annotations

import time
from typing import List, Optional, Tuple

from src.reasoning.reasoning_models import (
    CognitiveStateMode,
    Hypothesis,
    HypothesisStatus,
    Observation,
    ObservationCategory,
)
from src.reasoning.confidence_engine import ConfidenceEngine


class HypothesisManager:
    """
    Manages high-level hypotheses lifecycle and estimates overall CognitiveStateMode.
    """

    def evaluate_hypotheses(
        self, observations: List[Observation]
    ) -> Tuple[List[Hypothesis], CognitiveStateMode]:
        """
        Evaluate candidate hypotheses against active observations.
        Returns sorted hypotheses list and top estimated CognitiveStateMode.
        """
        hypotheses: List[Hypothesis] = []

        # 1. Searching for Object Hypothesis
        search_obs = [
            o for o in observations if o.category == ObservationCategory.BEHAVIOUR_PREDICTION and "search" in o.payload.get("current_activity", "").lower()
        ] + [
            o for o in observations if "where" in o.payload.get("transcript", "").lower() or "lost" in o.payload.get("transcript", "").lower()
        ]
        if search_obs:
            conf = ConfidenceEngine.combine_evidence(0.60, search_obs, [])
            hypotheses.append(
                Hypothesis(
                    title="User is searching for a misplaced object",
                    state_mode=CognitiveStateMode.SEARCHING,
                    confidence=conf,
                    supporting_observations=[o.observation_id for o in search_obs],
                    status=HypothesisStatus.ACTIVE if conf >= 0.50 else HypothesisStatus.CANDIDATE,
                )
            )

        # 2. Conversing Hypothesis
        speech_obs = [
            o for o in observations if o.category == ObservationCategory.VISION_FACE or "speech" in o.provenance.lower()
        ]
        if len(speech_obs) >= 2:
            conf = ConfidenceEngine.combine_evidence(0.75, speech_obs, [])
            hypotheses.append(
                Hypothesis(
                    title="User is conversing with a visitor or caregiver",
                    state_mode=CognitiveStateMode.CONVERSING,
                    confidence=conf,
                    supporting_observations=[o.observation_id for o in speech_obs],
                    status=HypothesisStatus.ACTIVE if conf >= 0.50 else HypothesisStatus.CANDIDATE,
                )
            )

        # 3. Following Daily Routine Hypothesis
        routine_obs = [
            o for o in observations if o.category in (ObservationCategory.ROUTINE_PATTERN, ObservationCategory.BEHAVIOUR_PREDICTION)
        ]
        if routine_obs:
            conf = ConfidenceEngine.combine_evidence(0.70, routine_obs, [])
            hypotheses.append(
                Hypothesis(
                    title="User is following a structured daily routine",
                    state_mode=CognitiveStateMode.FOLLOWING_ROUTINE,
                    confidence=conf,
                    supporting_observations=[o.observation_id for o in routine_obs],
                    status=HypothesisStatus.ACTIVE if conf >= 0.50 else HypothesisStatus.CANDIDATE,
                )
            )

        # Default fallback hypothesis
        if not hypotheses:
            hypotheses.append(
                Hypothesis(
                    title="User is quietly resting or idle",
                    state_mode=CognitiveStateMode.IDLE,
                    confidence=0.60,
                    supporting_observations=[],
                    status=HypothesisStatus.ACTIVE,
                )
            )

        # Sort hypotheses by confidence descending
        hypotheses.sort(key=lambda h: h.confidence, reverse=True)
        top_state = hypotheses[0].state_mode

        return hypotheses, top_state
