"""
MEMORA Deterministic FHIR Resource Adapter.

Converts simplified FHIR JSON-like dictionary structures into payload-neutral ClinicalRecord
objects and vice versa without external network requests or third-party FHIR dependencies.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, Optional

from src.interoperability.interoperability_models import (
    ClinicalProtocol,
    ClinicalRecord,
    ClinicalResourceType,
)


FHIR_RESOURCE_TYPE_MAP: Dict[str, ClinicalResourceType] = {
    "Patient": ClinicalResourceType.PATIENT,
    "Observation": ClinicalResourceType.OBSERVATION,
    "Condition": ClinicalResourceType.CONDITION,
    "MedicationStatement": ClinicalResourceType.MEDICATION,
    "Encounter": ClinicalResourceType.ENCOUNTER,
    "Device": ClinicalResourceType.DEVICE,
    "CarePlan": ClinicalResourceType.CARE_PLAN,
    "DetectedIssue": ClinicalResourceType.ALERT,
}

REVERSE_FHIR_MAP: Dict[ClinicalResourceType, str] = {
    v: k for k, v in FHIR_RESOURCE_TYPE_MAP.items()
}


class FHIRAdapter:
    """
    Thread-safe adapter for simplified FHIR resource conversions.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def parse_fhir_resource(self, raw_fhir: Dict[str, Any]) -> ClinicalRecord:
        """
        Convert a simplified FHIR JSON resource dict into a ClinicalRecord object.
        """
        res_type_str = raw_fhir.get("resourceType", "Observation")
        mapped_type = FHIR_RESOURCE_TYPE_MAP.get(res_type_str, ClinicalResourceType.OBSERVATION)

        ext_id = str(raw_fhir.get("id", "fhir-unknown-id"))
        payload_ref = raw_fhir.get("payload_reference") or f"fhir://{res_type_str}/{ext_id}"

        meta = {
            "status": raw_fhir.get("status", "final"),
            "code": raw_fhir.get("code", {}),
            "subject": raw_fhir.get("subject", {}),
        }

        with self._lock:
            return ClinicalRecord(
                protocol=ClinicalProtocol.FHIR,
                resource_type=mapped_type,
                external_identifier=ext_id,
                payload_reference=payload_ref,
                metadata=meta,
            )

    def export_fhir_resource(self, record: ClinicalRecord) -> Dict[str, Any]:
        """
        Convert an internal ClinicalRecord into a simplified FHIR resource dict.
        """
        res_type_str = REVERSE_FHIR_MAP.get(record.resource_type, "Observation")
        with self._lock:
            return {
                "resourceType": res_type_str,
                "id": record.external_identifier,
                "status": record.metadata.get("status", "final"),
                "code": record.metadata.get("code", {}),
                "payload_reference": record.payload_reference,
                "timestamp": record.timestamp,
            }
