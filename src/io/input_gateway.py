"""
MEMORA Input Gateway.

Receives external input notifications, normalizes message metadata, assigns unique
message identifiers, and associates session context without interpreting payload data.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from src.io.io_models import IOMessage, InputType


class InputGateway:
    """
    Thread-safe ingress gateway for normalizing external inputs.
    """

    def __init__(self) -> None:
        self._received_messages: List[IOMessage] = []
        self._lock = threading.Lock()

    def receive_input(
        self,
        source: str,
        input_type: InputType,
        payload_reference: str,
        destination: str = "CognitivePipeline",
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> IOMessage:
        msg = IOMessage(
            source=source,
            destination=destination,
            input_type=input_type,
            payload_reference=payload_reference,
            metadata=metadata or {},
            session_id=session_id,
        )
        with self._lock:
            self._received_messages.append(msg)
            return msg

    def get_received_messages(self) -> List[IOMessage]:
        with self._lock:
            return list(self._received_messages)

    def clear(self) -> None:
        with self._lock:
            self._received_messages.clear()
