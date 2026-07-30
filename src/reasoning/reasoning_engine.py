"""
MEMORA Central Cognitive Reasoning Engine.

Orchestrates multi-modal evidence fusion, uncertainty propagation, conflict resolution,
temporal reasoning, hypothesis generation, and explainable state estimation.

Serves as the central reasoning layer positioned above the Cognitive Operating System (Phase 21)
and below the Behaviour Intelligence Platform (Phase 23).
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from src.core.interfaces import ICognitiveSubsystem
from src.reasoning.reasoning_models import (
    CognitiveStateMode,
    ConflictRecord,
    Hypothesis,
    Observation,
    ObservationCategory,
)
from src.reasoning.blackboard import CognitiveBlackboard
from src.reasoning.conflict_detector import ConflictDetector
from src.reasoning.hypothesis_manager import HypothesisManager
from src.reasoning.explanation_builder import ExplanationBuilder
from src.reasoning.temporal_reasoner import TemporalReasoner


class CognitiveReasoningEngine(ICognitiveSubsystem):
    """
    Central Cognitive Reasoning Engine.
    """

    def __init__(self) -> None:
        self.blackboard = CognitiveBlackboard()
        self.hypothesis_manager = HypothesisManager()
        self._cycle_counter = 0
        self._status = "INITIALIZED"
        self._lock = threading.RLock()

    def initialize(self) -> bool:
        with self._lock:
            self._status = "RUNNING"
            return True

    def shutdown(self) -> bool:
        with self._lock:
            self._status = "SHUTDOWN"
            self.blackboard.clear()
            return True

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.reason(
            event_name=input_data.get("event_name"),
            location=input_data.get("location", "Living Room"),
            user_speech=input_data.get("user_speech"),
            patient_state_mode=input_data.get("patient_state_mode", "Calm"),
            active_goal_name=input_data.get("active_goal_name"),
        )

    def status(self) -> str:
        with self._lock:
            return self._status

    def health(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "status": self._status,
                "active_observations": len(self.blackboard.get_active_observations()),
            }

    def metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {"cycle_count": self._cycle_counter}

    def explain(self) -> str:
        hyps = self.blackboard.get_hypotheses()
        if hyps:
            return f"Reasoning Engine: Primary state is '{hyps[0].state_mode.value}' (Confidence: {hyps[0].confidence:.0%})."
        return "Reasoning Engine: Baseline idle state."

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
        Post a multi-modal observation to the blackboard workspace.
        """
        return self.blackboard.post_observation(
            source=source,
            category=category,
            payload=payload,
            confidence=confidence,
            importance=importance,
            expiry_seconds=expiry_seconds,
            provenance=provenance,
            reasoning_tags=reasoning_tags,
        )

    def reason(
        self,
        event_name: Optional[str] = None,
        location: str = "Living Room",
        user_speech: Optional[str] = None,
        patient_state_mode: str = "Calm",
        active_goal_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute one cycle of cognitive multi-modal reasoning.

        Returns
        -------
        Dict[str, Any]
            Complete serialisable reasoning summary payload.
        """
        start_ts = time.time()
        with self._lock:
            self._cycle_counter += 1

        # 1. Ingest immediate cycle observations if present
        if event_name:
            self.post_observation(
                source="FaceRecognizer",
                category=ObservationCategory.VISION_FACE,
                payload={"person_name": event_name, "location": location},
                confidence=0.92,
                provenance="Camera Pipeline",
            )
        if user_speech:
            self.post_observation(
                source="SpeechEngine",
                category=ObservationCategory.SENSOR_HAL,
                payload={"transcript": user_speech, "location": location},
                confidence=0.88,
                provenance="Microphone HAL",
            )
        if active_goal_name:
            self.post_observation(
                source="GoalManager",
                category=ObservationCategory.GOAL_STATE,
                payload={"goal_name": active_goal_name, "status": "ACTIVE"},
                confidence=0.85,
                provenance="Cognitive Operating System",
            )

        # 2. Prune expired observations
        self.blackboard.prune_expired()

        # 3. Retrieve active observations
        active_obs = self.blackboard.get_active_observations()

        # 4. Detect conflicts
        conflicts = ConflictDetector.detect_conflicts(active_obs)
        for c in conflicts:
            self.blackboard.record_conflict(c)

        # 5. Evaluate Hypotheses & Estimate Cognitive State
        hypotheses, state_mode = self.hypothesis_manager.evaluate_hypotheses(active_obs)
        self.blackboard.set_hypotheses(hypotheses)

        top_hyp = hypotheses[0]

        # 6. Build Explainable Reasoning Graph & Narrative
        supp_obs = [obs for obs in active_obs if obs.observation_id in top_hyp.supporting_observations]
        graph_nodes, narrative = ExplanationBuilder.build_reasoning_graph(
            estimated_state=state_mode,
            top_hypothesis=top_hyp,
            supporting_observations=supp_obs,
        )

        latency_ms = round((time.time() - start_ts) * 1000.0, 3)

        return {
            "cycle": self._cycle_counter,
            "cognitive_state": state_mode.value,
            "top_hypothesis": top_hyp.to_dict(),
            "hypotheses_count": len(hypotheses),
            "hypotheses": [h.to_dict() for h in hypotheses[:3]],
            "active_observations_count": len(active_obs),
            "conflicts_count": len(conflicts),
            "conflicts": [c.to_dict() for c in conflicts[:3]],
            "reasoning_graph": [n.to_dict() for n in graph_nodes],
            "explanation_narrative": narrative,
            "reasoning_latency_ms": latency_ms,
        }

    def reset(self) -> None:
        with self._lock:
            self.blackboard.clear()
            self._cycle_counter = 0
