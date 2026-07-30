"""
MEMORA Output Gateway.

Normalizes delivery metadata and prepares deterministic outbound IOMessage envelopes.
Does not execute physical transport, network protocols, or hardware driver writes.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from src.io.io_models import IOMessage, OutputType


class OutputGateway:
    """
    Thread-safe egress gateway for preparing standardized outbound outputs.
    """

    def __init__(self) -> None:
        self._sent_messages: List[IOMessage] = []
        self._lock = threading.Lock()

    def prepare_output(
        self,
        destination: str,
        output_type: OutputType,
        payload_reference: str,
        source: str = "CognitivePipeline",
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> IOMessage:
        msg = IOMessage(
            source=source,
            destination=destination,
            output_type=output_type,
            payload_reference=payload_reference,
            metadata=metadata or {},
            session_id=session_id,
        )
        with self._lock:
            self._sent_messages.append(msg)
            return msg

    def get_sent_messages(self) -> List[IOMessage]:
        with self._lock:
            return list(self._sent_messages)

    def clear(self) -> None:
        with self._lock:
            self._sent_messages.clear()
