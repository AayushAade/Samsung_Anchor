"""
MEMORA Failure Analyzer.

Generates structured, actionable failure analysis records for unsuccessful plan executions:
Identifies root causes, missing evidence, incorrect assumptions, sensor limitations,
interruption causes, and planning weaknesses.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.experience.experience_models import ExecutionOutcome, ExecutionRecord, FailureAnalysisRecord


class FailureAnalyzer:
    """
    Analyzes execution failures and extracts root causes.
    """

    @classmethod
    def analyze_failure(
        cls,
        record: ExecutionRecord,
        divergence_reason: Optional[str] = None,
        error_details: Optional[str] = None,
    ) -> FailureAnalysisRecord:
        """
        Produce a structured FailureAnalysisRecord for an unsuccessful execution.
        """
        missing_evidence: List[str] = []
        assumptions: List[str] = []
        sensor_limits: List[str] = []
        interrupts: List[str] = []
        weaknesses: List[str] = []

        root_cause = "General Execution Divergence"

        if divergence_reason:
            if "room" in divergence_reason.lower():
                root_cause = "Environmental Reality Divergence (Room Transition)"
                assumptions.append("Assumed user would remain in initial room throughout plan execution.")
            elif "timeout" in divergence_reason.lower():
                root_cause = "Execution Duration Timeout"
                weaknesses.append("Task estimated duration was under-budgeted.")

        if record.interruptions:
            root_cause = f"External Interruption ({record.interruptions[0].get('interrupt_type', 'Interrupt')})"
            interrupts.append(str(record.interruptions[0]))

        if error_details and "sensor" in error_details.lower():
            root_cause = "Sensor Confidence Degradation"
            sensor_limits.append(error_details)

        explanation = (
            f"Failure Analysis for Execution `{record.execution_id}` (Goal: {record.goal_id}): "
            f"Root Cause: {root_cause}. "
            f"Status: {record.completion_status.value}."
        )

        return FailureAnalysisRecord(
            execution_id=record.execution_id,
            root_cause=root_cause,
            missing_evidence=missing_evidence,
            incorrect_assumptions=assumptions,
            sensor_limitations=sensor_limits,
            interruption_causes=interrupts,
            planning_weaknesses=weaknesses,
            recovery_effectiveness="RECOVERED" if record.recovery_actions else "FAILED",
            explanation=explanation,
        )
