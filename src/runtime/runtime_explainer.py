"""
MEMORA Runtime Trace Explainer & Structured Logging Framework.

Provides structured JSON logging contracts and end-to-end distributed trace explanations:
Perception -> Trust -> Behaviour -> Experience -> Memory -> Knowledge -> Reasoning -> Executive -> Application
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List


class RuntimeExplainer:
    """
    Generates structured JSON logs and end-to-end distributed trace narratives.
    """

    @classmethod
    def create_structured_log(
        cls,
        subsystem: str,
        operation: str,
        correlation_id: str,
        severity: str = "INFO",
        execution_duration_ms: float = 0.0,
        trace_id: str = "trc-main",
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Produce a JSON-formatted structured log string.
        """
        payload = {
            "timestamp": datetime.now().isoformat(),
            "subsystem": subsystem,
            "operation": operation,
            "correlation_id": correlation_id,
            "severity": severity,
            "execution_duration_ms": round(execution_duration_ms, 3),
            "trace_id": trace_id,
            "metadata": metadata or {},
        }
        return json.dumps(payload)

    @classmethod
    def generate_trace_explanation(cls, trace_id: str, trace_steps: List[Dict[str, Any]]) -> str:
        """
        Produce a human-readable Markdown narrative explaining an end-to-end execution trace.
        """
        lines = [
            f"### MEMORA Distributed Execution Trace `{trace_id}`",
            f"- **Trace Steps Count**: {len(trace_steps)}",
            "",
            "**Subsystem Step Sequence**:",
        ]
        for step in trace_steps:
            sub = step.get("subsystem", "Subsystem")
            dur = step.get("duration_ms", 0.0)
            status = step.get("status", "OK")
            lines.append(f"  1. **{sub}**: Executed in {dur:.2f}ms [{status}]")

        return "\n".join(lines)
