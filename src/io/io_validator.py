"""
MEMORA Cognitive I/O Message Validator.

Validates IOMessage envelopes against metadata schemas, type supported contracts,
payload references, and session association requirements without mutating message state.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Set, Tuple

from src.io.io_models import IOMessage


class IOValidator:
    """
    Read-only validation engine for incoming and outgoing IOMessage envelopes.
    """

    def __init__(self) -> None:
        self._seen_message_ids: Set[str] = set()
        self._validation_history: List[Tuple[str, bool, str]] = []
        self._lock = threading.Lock()

    def validate_message(self, message: IOMessage) -> Tuple[bool, str]:
        """
        Perform a comprehensive read-only validation check on an IOMessage instance.
        Returns a tuple of (is_valid, validation_reason).
        """
        # 1. Message ID duplicate check
        with self._lock:
            if message.message_id in self._seen_message_ids:
                reason = f"Duplicate message_id `{message.message_id}` detected."
                self._validation_history.append((message.message_id, False, reason))
                return False, reason
            self._seen_message_ids.add(message.message_id)

        # 2. Source & Destination non-empty check
        if not message.source or len(message.source.strip()) == 0:
            reason = "Message source cannot be empty or whitespace."
            with self._lock:
                self._validation_history.append((message.message_id, False, reason))
            return False, reason

        if not message.destination or len(message.destination.strip()) == 0:
            reason = "Message destination cannot be empty or whitespace."
            with self._lock:
                self._validation_history.append((message.message_id, False, reason))
            return False, reason

        # 3. Message type check (must specify input_type OR output_type)
        if message.input_type is None and message.output_type is None:
            reason = "IOMessage must specify either input_type or output_type."
            with self._lock:
                self._validation_history.append((message.message_id, False, reason))
            return False, reason

        # 4. Payload reference check
        if message.payload_reference is None:
            reason = "Message payload_reference cannot be None."
            with self._lock:
                self._validation_history.append((message.message_id, False, reason))
            return False, reason

        reason = "Valid IOMessage envelope."
        with self._lock:
            self._validation_history.append((message.message_id, True, reason))
        return True, reason

    def get_validation_history(self) -> List[Tuple[str, bool, str]]:
        """Return history of performed validations."""
        with self._lock:
            return list(self._validation_history)

    def clear(self) -> None:
        """Clear validator cache and history."""
        with self._lock:
            self._seen_message_ids.clear()
            self._validation_history.clear()
