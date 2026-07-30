"""
MEMORA Confidence Calibrator.

Compares predicted plan confidence against historical execution success rates and variance.
Generates calibrated confidence recommendations for executive planning without mutating
upstream reasoning algorithms.
"""

from __future__ import annotations

from typing import List, Optional

from src.experience.experience_models import CalibratedConfidence, ExecutionRecord
from src.experience.pattern_library import PatternLibrary


class ConfidenceCalibrator:
    """
    Calibrates confidence scores based on empirical execution histories.
    """

    @classmethod
    def calibrate_confidence(
        cls,
        goal_title: str,
        predicted_confidence: float,
        pattern_library: PatternLibrary,
    ) -> CalibratedConfidence:
        """
        Produce a CalibratedConfidence recommendation for a plan given its goal title.
        """
        pattern = pattern_library.find_recommended_pattern(goal_title)

        if not pattern or pattern.usage_count < 2:
            return CalibratedConfidence(
                predicted_confidence=predicted_confidence,
                historical_success_rate=predicted_confidence,
                execution_variance=0.0,
                recommended_confidence=predicted_confidence,
                calibration_explanation="Insufficient historical execution data; retaining baseline predicted confidence.",
            )

        hist_rate = pattern.success_rate
        variance = abs(predicted_confidence - hist_rate)

        # Weighted combination: 50% predicted + 50% empirical historical success
        calibrated = round(0.50 * predicted_confidence + 0.50 * hist_rate, 3)

        explanation = (
            f"Calibrated confidence for '{goal_title}': "
            f"Predicted ({predicted_confidence:.0%}) adjusted by historical success rate ({hist_rate:.0%}) "
            f"across {pattern.usage_count} executions. Recommended: {calibrated:.0%}."
        )

        return CalibratedConfidence(
            predicted_confidence=predicted_confidence,
            historical_success_rate=hist_rate,
            execution_variance=variance,
            recommended_confidence=calibrated,
            calibration_explanation=explanation,
        )
