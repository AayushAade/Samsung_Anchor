"""
MEMORA Clinical Interoperability Validator.

Validates ClinicalRecord objects against protocol standards, mandatory external IDs,
payload reference integrity, and uniqueness constraints without mutating record state.
"""

from __future__ import annotations

import threading
from typing import Set, Tuple

from src.interoperability.interoperability_models import ClinicalRecord


class InteroperabilityValidator:
    """
    Read-only validator for ClinicalRecord instances.
    """

    def __init__(self) -> None:
        self._seen_record_ids: Set[str] = set()
        self._lock = threading.Lock()

    def validate_record(self, record: ClinicalRecord) -> Tuple[bool, str]:
        """
        Perform read-only validation check on a ClinicalRecord.
        Returns (is_valid, reason_string).
        """
        # 1. Duplicate record_id check
        with self._lock:
            if record.record_id in self._seen_record_ids:
                return False, f"Duplicate record_id `{record.record_id}` detected."
            self._seen_record_ids.add(record.record_id)

        # 2. External identifier check
        if not record.external_identifier or len(record.external_identifier.strip()) == 0:
            return False, "ClinicalRecord external_identifier cannot be empty."

        # 3. Payload reference check
        if not record.payload_reference or len(record.payload_reference.strip()) == 0:
            return False, "ClinicalRecord payload_reference cannot be empty."

        # 4. Protocol and resource_type validity check
        if record.protocol is None:
            return False, "ClinicalRecord protocol cannot be None."
        if record.resource_type is None:
            return False, "ClinicalRecord resource_type cannot be None."

        return True, "Valid ClinicalRecord."

    def clear(self) -> None:
        """Clear cached record IDs."""
        with self._lock:
            self._seen_record_ids.clear()
