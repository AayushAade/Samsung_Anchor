"""
MEMORA Unified Data Contracts.

Provides shared canonical data contracts referencing common representations across
Perception, Memory, COS, Reasoning, Executive, Experience, and Trust layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class SharedContext:
    location: str = "Living Room"
    time_of_day: str = "Morning"
    patient_name: str = "Margaret"
    active_person: Optional[str] = None
    user_speech: Optional[str] = None
    timestamp_iso: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SharedDecision:
    subsystem: str
    decision_type: str
    confidence: float
    rationale: str
    action_message: str
    timestamp_iso: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subsystem": self.subsystem,
            "decision_type": self.decision_type,
            "confidence": round(self.confidence, 3),
            "rationale": self.rationale,
            "action_message": self.action_message,
            "timestamp_iso": self.timestamp_iso,
        }
