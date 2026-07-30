"""
MEMORA Unified Cognitive Input/Output (I/O) Data Models.

Defines immutable value objects, message enums, routing decisions, and snapshot schemas
for external interaction boundaries.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class InputType(str, Enum):
    """
    Standardized classification for external input sources.
    """

    CAMERA = "CAMERA"
    MICROPHONE = "MICROPHONE"
    SENSOR = "SENSOR"
    TEXT = "TEXT"
    SYSTEM = "SYSTEM"
    CLINICAL = "CLINICAL"
    EXTERNAL = "EXTERNAL"


class OutputType(str, Enum):
    """
    Standardized classification for cognitive egress output channels.
    """

    DISPLAY = "DISPLAY"
    AUDIO = "AUDIO"
    ALERT = "ALERT"
    LOG = "LOG"
    REPORT = "REPORT"
    SYSTEM = "SYSTEM"
    CLINICAL = "CLINICAL"


@dataclass
class IOMessage:
    """
    Standardized payload-neutral message envelope for incoming and outgoing data.
    """

    source: str
    destination: str
    input_type: Optional[InputType] = None
    output_type: Optional[OutputType] = None
    payload_reference: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    message_id: str = field(default_factory=lambda: f"msg-{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def is_input(self) -> bool:
        """Return True if message represents an ingress input message."""
        return self.input_type is not None

    def is_output(self) -> bool:
        """Return True if message represents an egress output message."""
        return self.output_type is not None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize IOMessage dataclass to a dictionary representation."""
        return {
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "source": self.source,
            "destination": self.destination,
            "input_type": self.input_type.value if self.input_type else None,
            "output_type": self.output_type.value if self.output_type else None,
            "payload_reference": self.payload_reference,
            "metadata": dict(self.metadata),
            "session_id": self.session_id,
        }


@dataclass
class RoutingDecision:
    """
    Represents the result of a deterministic message routing evaluation.
    """

    destination: str
    accepted: bool
    reason: str
    validation_status: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize RoutingDecision to a dictionary representation."""
        return {
            "destination": self.destination,
            "accepted": self.accepted,
            "reason": self.reason,
            "validation_status": self.validation_status,
        }


@dataclass
class IOSnapshot:
    """
    Point-in-time snapshot of I/O message traffic statistics and checksum.
    """

    received_messages_count: int
    sent_messages_count: int
    routed_messages_count: int
    rejected_messages_count: int
    checksum: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize IOSnapshot to a dictionary representation."""
        return {
            "timestamp": self.timestamp,
            "received_messages_count": self.received_messages_count,
            "sent_messages_count": self.sent_messages_count,
            "routed_messages_count": self.routed_messages_count,
            "rejected_messages_count": self.rejected_messages_count,
            "checksum": self.checksum,
        }
