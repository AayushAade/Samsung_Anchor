"""
MEMORA Cognitive Decision Timeline & Confidence Model.

Generates step-by-step observable decision timelines for every cognitive cycle
and maps raw numerical confidence scores to human-friendly clinical labels.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any


class ConfidenceLevel(str, Enum):
    HIGH = "High Confidence"
    MEDIUM = "Medium Confidence"
    LOW = "Low Confidence"
    UNCERTAIN = "Uncertain"

    @classmethod
    def from_score(cls, score: float) -> ConfidenceLevel:
        """Map raw 0.0-1.0 numerical score to friendly clinical label."""
        if score >= 0.85:
            return cls.HIGH
        elif score >= 0.65:
            return cls.MEDIUM
        elif score >= 0.40:
            return cls.LOW
        return cls.UNCERTAIN


@dataclass
class TimelineStage:
    """Represents a single processing stage in a cognitive decision timeline."""
    subsystem: str
    decision: str
    reason: str
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    duration_ms: float = 0.0
    timestamp_iso: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


class CognitiveDecisionTimeline:
    """
    Timeline generator capturing the end-to-end reasoning sequence of a cognitive cycle.
    """

    def __init__(self, cycle_id: int | str = 1) -> None:
        self.cycle_id = cycle_id
        self.start_time = time.perf_counter()
        self.stages: list[TimelineStage] = []

    def add_stage(
        self,
        subsystem: str,
        decision: str,
        reason: str,
        confidence_score: float = 1.0,
        duration_ms: float = 0.0,
    ) -> None:
        """Add a stage to the cognitive decision timeline."""
        stage = TimelineStage(
            subsystem=subsystem,
            decision=decision,
            reason=reason,
            confidence=ConfidenceLevel.from_score(confidence_score),
            duration_ms=duration_ms,
        )
        self.stages.append(stage)

    def to_dict(self) -> dict[str, Any]:
        """Convert timeline to dictionary payload."""
        total_duration_ms = (time.perf_counter() - self.start_time) * 1000.0
        return {
            "cycle_id": self.cycle_id,
            "total_duration_ms": total_duration_ms,
            "stage_count": len(self.stages),
            "stages": [
                {
                    "timestamp": s.timestamp_iso,
                    "subsystem": s.subsystem,
                    "decision": s.decision,
                    "reason": s.reason,
                    "confidence": s.confidence.value,
                    "duration_ms": s.duration_ms,
                }
                for s in self.stages
            ],
        }

    def generate_markdown(self) -> str:
        """Generate formatted Markdown timeline for clinical review or judge presentation."""
        lines = [
            f"### Cognitive Decision Timeline (Cycle #{self.cycle_id})",
            "",
            "| Step | Subsystem | Decision | Clinical Rationale | Confidence | Latency (ms) |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for idx, s in enumerate(self.stages, 1):
            lines.append(
                f"| {idx} | {s.subsystem} | **{s.decision}** | {s.reason} | {s.confidence.value} | {s.duration_ms:.2f} |"
            )
        return "\n".join(lines)
