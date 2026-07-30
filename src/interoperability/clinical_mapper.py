"""
MEMORA Clinical Mapper.

Translates between ClinicalRecord objects and payload-neutral IOMessage envelopes.
Performs deterministic protocol/schema mapping without cognition or reasoning.
"""

from __future__ import annotations

import threading
from typing import Dict, Optional

from src.interoperability.interoperability_models import (
    ClinicalProtocol,
    ClinicalRecord,
    ClinicalResourceType,
)
from src.io.io_models import IOMessage, InputType, OutputType


RESOURCE_TO_INPUT_TYPE: Dict[ClinicalResourceType, InputType] = {
    ClinicalResourceType.PATIENT: InputType.CLINICAL,
    ClinicalResourceType.OBSERVATION: InputType.CLINICAL,
    ClinicalResourceType.CONDITION: InputType.CLINICAL,
    ClinicalResourceType.MEDICATION: InputType.CLINICAL,
    ClinicalResourceType.ENCOUNTER: InputType.SYSTEM,
    ClinicalResourceType.DEVICE: InputType.SENSOR,
    ClinicalResourceType.CARE_PLAN: InputType.CLINICAL,
    ClinicalResourceType.ALERT: InputType.CLINICAL,
}

RESOURCE_TO_OUTPUT_TYPE: Dict[ClinicalResourceType, OutputType] = {
    ClinicalResourceType.PATIENT: OutputType.REPORT,
    ClinicalResourceType.OBSERVATION: OutputType.CLINICAL,
    ClinicalResourceType.CONDITION: OutputType.REPORT,
    ClinicalResourceType.MEDICATION: OutputType.REPORT,
    ClinicalResourceType.ENCOUNTER: OutputType.LOG,
    ClinicalResourceType.DEVICE: OutputType.SYSTEM,
    ClinicalResourceType.CARE_PLAN: OutputType.REPORT,
    ClinicalResourceType.ALERT: OutputType.ALERT,
}


class ClinicalMapper:
    """
    Thread-safe mapper converting ClinicalRecords to/from IOMessage envelopes.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def record_to_io_message(
        self,
        record: ClinicalRecord,
        destination: str = "CognitivePipeline",
        session_id: Optional[str] = None,
    ) -> IOMessage:
        """
        Map a ClinicalRecord to an ingress IOMessage envelope.
        """
        inp_type = RESOURCE_TO_INPUT_TYPE.get(record.resource_type, InputType.CLINICAL)
        source_id = f"ClinicalGateway:{record.protocol.value}:{record.external_identifier}"

        meta = {
            "protocol": record.protocol.value,
            "resource_type": record.resource_type.value,
            "external_id": record.external_identifier,
            "record_id": record.record_id,
        }
        meta.update(record.metadata)

        with self._lock:
            return IOMessage(
                source=source_id,
                destination=destination,
                input_type=inp_type,
                payload_reference=record.payload_reference,
                metadata=meta,
                session_id=session_id,
            )

    def io_message_to_record(
        self,
        io_message: IOMessage,
        target_protocol: ClinicalProtocol = ClinicalProtocol.FHIR,
    ) -> ClinicalRecord:
        """
        Map an outbound IOMessage envelope to a ClinicalRecord object.
        """
        res_type_str = io_message.metadata.get("resource_type", "OBSERVATION")
        try:
            mapped_res_type = ClinicalResourceType[res_type_str]
        except KeyError:
            mapped_res_type = ClinicalResourceType.OBSERVATION

        ext_id = io_message.metadata.get("external_id", f"ext-{io_message.message_id}")

        with self._lock:
            return ClinicalRecord(
                protocol=target_protocol,
                resource_type=mapped_res_type,
                external_identifier=ext_id,
                payload_reference=io_message.payload_reference,
                metadata=dict(io_message.metadata),
            )
