"""
MEMORA Outcome Evaluation Analyzer.

Classifies completed plan executions into standard outcome categories:
SUCCESSFUL, PARTIALLY_SUCCESSFUL, RECOVERED, INTERRUPTED, FAILED, ABORTED, UNKNOWN
and generates structured evaluation summaries.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from src.experience.experience_models import ExecutionOutcome, ExecutionRecord


class OutcomeAnalyzer:
    """
    Evaluates completed execution plans and determines outcome classification.
    """

    @classmethod
    def evaluate_execution(
        cls,
        tasks_executed: List[Dict[str, Any]],
        interruptions: List[Dict[str, Any]],
        recovery_actions: List[Dict[str, Any]],
        has_failed_task: bool = False,
    ) -> Tuple[ExecutionOutcome, str]:
        """
        Classify execution outcome and produce narrative explanation.
        """
        if interruptions:
            return (
                ExecutionOutcome.INTERRUPTED,
                f"Execution interrupted by external event ({interruptions[0].get('interrupt_type', 'Interrupt')}). Context preserved.",
            )

        if recovery_actions and not has_failed_task:
            return (
                ExecutionOutcome.RECOVERED,
                f"Execution successfully recovered via {recovery_actions[0].get('strategy', 'Recovery')} strategy.",
            )

        if has_failed_task:
            if any(t.get("status") == "COMPLETED" for t in tasks_executed):
                return (
                    ExecutionOutcome.PARTIALLY_SUCCESSFUL,
                    "Execution partially completed; primary tasks succeeded while secondary step failed.",
                )
            return (
                ExecutionOutcome.FAILED,
                "Execution failed; task duration or dependency bounds exceeded.",
            )

        return ExecutionOutcome.SUCCESSFUL, "Execution completed successfully without errors or interruptions."
