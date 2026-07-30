"""
MEMORA Standardized Event Contract.

Provides versioned, structured UnifiedEvent contracts standardizing inter-subsystem payload delivery:
- Origin, destination, and priority routing
- Correlation IDs for transaction tracking
- Confidence scores and metadata payloads
- Versioning support ("1.0.0")
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class UnifiedEvent:
    """
    Standardized inter-subsystem event contract.
    """

    origin: str
    destination: str
    priority: float = 0.50
    confidence: float = 1.0
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: str = field(default_factory=lambda: f"corr-{uuid.uuid4().hex[:8]}")
    event_id: str = field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:8]}")
    timestamp_iso: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "version": self.version,
            "origin": self.origin,
            "destination": self.destination,
            "priority": round(self.priority, 3),
            "confidence": round(self.confidence, 3),
            "correlation_id": self.correlation_id,
            "timestamp_iso": self.timestamp_iso,
            "payload": self.payload,
            "metadata": self.metadata,
        }
