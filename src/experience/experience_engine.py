"""
MEMORA Central Experience Engine.

Orchestrates experience acquisition, append-only repository persistence,
outcome evaluation, pattern library extraction, success metrics generation,
failure analysis, confidence calibration, routine optimization, and caregiver preferences.

Positioned as a dedicated experience subsystem between Cognitive Reasoning (Phase 24)
and Behaviour Intelligence (Phase 23).
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from src.core.interfaces import ICognitiveSubsystem
from src.experience.experience_models import ExecutionOutcome, ExecutionRecord
from src.experience.experience_repository import ExperienceRepository
from src.experience.execution_history import ExecutionHistoryIndex
from src.experience.pattern_library import PatternLibrary
from src.experience.experience_analyzer import OutcomeAnalyzer
from src.experience.success_metrics import SuccessMetricsEngine
from src.experience.failure_analyzer import FailureAnalyzer
from src.experience.confidence_calibrator import ConfidenceCalibrator
from src.experience.routine_optimizer import RoutineOptimizer
from src.experience.preference_manager import CaregiverPreferenceManager
from src.experience.experience_explainer import ExperienceExplainer


class ExperienceEngine(ICognitiveSubsystem):
    """
    Central Experience Subsystem Orchestrator.
    """

    def __init__(self) -> None:
        self.repository = ExperienceRepository()
        self.history_index = ExecutionHistoryIndex(self.repository)
        self.pattern_library = PatternLibrary()
        self.preference_manager = CaregiverPreferenceManager()
        self.routine_optimizer = RoutineOptimizer(self.pattern_library)
        self._cycle_counter = 0
        self._status = "INITIALIZED"
        self._lock = threading.Lock()

    def initialize(self) -> bool:
        with self._lock:
            self._status = "RUNNING"
            return True

    def shutdown(self) -> bool:
        with self._lock:
            self._status = "SHUTDOWN"
            return True

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.process_cycle(
            executive_summary=input_data.get("executive_summary"),
            reasoning_summary=input_data.get("reasoning_summary"),
            location=input_data.get("location", "Living Room"),
        )

    def status(self) -> str:
        with self._lock:
            return self._status

    def health(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "status": self._status,
                "total_records": len(self.repository.get_all_records()),
            }

    def metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {"cycle_count": self._cycle_counter}

    def explain(self) -> str:
        records = self.repository.get_recent_records(limit=1)
        if records:
            return f"Experience Subsystem: Last execution status was '{records[0].completion_status.value}'."
        return "Experience Subsystem: Ready to record execution patterns."

    def process_cycle(
        self,
        executive_summary: Optional[Dict[str, Any]] = None,
        reasoning_summary: Optional[Dict[str, Any]] = None,
        location: str = "Living Room",
    ) -> Dict[str, Any]:
        """
        Execute one cycle of experience recording, analysis, and recommendation.

        Returns
        -------
        Dict[str, Any]
            Serialisable experience summary dictionary.
        """
        start_ts = time.time()
        with self._lock:
            self._cycle_counter += 1

        # 1. Record completed execution if executive summary present
        if executive_summary and "active_plan" in executive_summary:
            plan_info = executive_summary["active_plan"]
            top_goal = executive_summary.get("top_goal", {})
            goal_title = top_goal.get("title", "Assistive Goal")

            # Determine outcome
            has_div = executive_summary.get("has_divergence", False)
            is_int = executive_summary.get("is_interrupted", False)

            if is_int:
                outcome = ExecutionOutcome.INTERRUPTED
            elif has_div:
                outcome = ExecutionOutcome.FAILED
            else:
                outcome = ExecutionOutcome.SUCCESSFUL

            rec = ExecutionRecord(
                goal_id=top_goal.get("goal_id", "g1"),
                plan_id=plan_info.get("plan_id", "p1"),
                tasks_executed=plan_info.get("tasks", []),
                completion_status=outcome,
                confidence_evolution=[plan_info.get("confidence", 0.80)],
                latency_ms=executive_summary.get("planning_latency_ms", 1.0),
                environment_context={"room": location},
            )

            # Append to Repository
            self.repository.add_record(rec)

            # Update Pattern Library
            pattern = self.pattern_library.update_from_execution(rec, goal_title=goal_title)

            # Analyze failure if applicable
            if outcome == ExecutionOutcome.FAILED:
                FailureAnalyzer.analyze_failure(rec, divergence_reason=executive_summary.get("divergence_reason"))

        # 2. Compute Success Metrics
        metrics = SuccessMetricsEngine.compute_metrics(self.repository)

        # 3. Calibrate Confidence for current top goal
        current_goal = executive_summary.get("top_goal", {}).get("title", "Assistive Goal") if executive_summary else "Assistive Goal"
        calibration = ConfidenceCalibrator.calibrate_confidence(
            goal_title=current_goal,
            predicted_confidence=0.85,
            pattern_library=self.pattern_library,
        )

        # 4. Generate Narrative Explanation
        top_pat = self.pattern_library.find_recommended_pattern(current_goal)
        if top_pat:
            narrative = ExperienceExplainer.generate_recommendation_explanation(top_pat, calibration)
        else:
            narrative = f"Accumulating baseline execution records for goal '{current_goal}'."

        latency_ms = round((time.time() - start_ts) * 1000.0, 3)

        return {
            "cycle": self._cycle_counter,
            "total_records_count": len(self.repository.get_all_records()),
            "success_metrics": metrics,
            "calibrated_confidence": calibration.to_dict(),
            "patterns_count": len(self.pattern_library.get_all_patterns()),
            "top_pattern": top_pat.to_dict() if top_pat else None,
            "explanation_narrative": narrative,
            "experience_latency_ms": latency_ms,
        }

    def reset(self) -> None:
        with self._lock:
            self._cycle_counter = 0
            self.repository.clear()
            self.repository._seed_baseline_history()
