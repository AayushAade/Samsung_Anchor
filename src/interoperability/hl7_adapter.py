"""
MEMORA Deterministic HL7 Message Adapter.

Converts simplified HL7 v2 pipe-delimited segment messages into payload-neutral
ClinicalRecord objects and vice versa without network sockets or MLLP drivers.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, Optional

from src.interoperability.interoperability_models import (
    ClinicalProtocol,
    ClinicalRecord,
    ClinicalResourceType,
)


HL7_EVENT_MAP: Dict[str, ClinicalResourceType] = {
    "ADT^A08": ClinicalResourceType.PATIENT,
    "ORU^R01": ClinicalResourceType.OBSERVATION,
    "PPR^PC1": ClinicalResourceType.CARE_PLAN,
    "MDM^T02": ClinicalResourceType.ALERT,
    "SIU^S12": ClinicalResourceType.ENCOUNTER,
}


class HL7Adapter:
    """
    Thread-safe adapter for simplified HL7 message conversions.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def parse_hl7_message(self, raw_hl7: str) -> ClinicalRecord:
        """
        Parse a simplified HL7 v2 pipe-delimited message string into a ClinicalRecord object.
        """
        segments = raw_hl7.strip().split("\n")
        msh_fields = segments[0].split("|") if segments else []

        event_code = "ORU^R01"
        if len(msh_fields) > 8:
            event_code = msh_fields[8]

        mapped_type = HL7_EVENT_MAP.get(event_code, ClinicalResourceType.OBSERVATION)
        ext_id = msh_fields[9] if len(msh_fields) > 9 else "hl7-msg-001"
        payload_ref = f"hl7://{event_code}/{ext_id}"

        meta = {
            "sending_app": msh_fields[2] if len(msh_fields) > 2 else "EMR",
            "event_code": event_code,
        }

        with self._lock:
            return ClinicalRecord(
                protocol=ClinicalProtocol.HL7,
                resource_type=mapped_type,
                external_identifier=ext_id,
                payload_reference=payload_ref,
                metadata=meta,
            )

    def export_hl7_message(self, record: ClinicalRecord) -> str:
        """
        Export an internal ClinicalRecord into a simplified pipe-delimited HL7 string.
        """
        event_code = record.metadata.get("event_code", "ORU^R01")
        sending_app = record.metadata.get("sending_app", "MEMORA")
        ext_id = record.external_identifier

        with self._lock:
            msh = f"MSH|^~\\&|{sending_app}|HOSPITAL|RECEIVER|FACILITY|{record.timestamp}||{event_code}|{ext_id}|P|2.5"
            obx = f"OBX|1|ST|{record.resource_type.value}||{record.payload_reference}||||||F"
            return f"{msh}\n{obx}"
