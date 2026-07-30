"""
MEMORA Central Clinical Interoperability Engine.

Public façade coordinating FHIRAdapter, HL7Adapter, ClinicalMapper, and InteroperabilityValidator.
Provides unified entry points for clinical record import, export, translation, and snapshotting.
"""

from __future__ import annotations

import hashlib
import json
import threading
from typing import Any, Dict, List, Optional, Tuple

from src.interoperability.clinical_mapper import ClinicalMapper
from src.interoperability.fhir_adapter import FHIRAdapter
from src.interoperability.hl7_adapter import HL7Adapter
from src.interoperability.interoperability_models import (
    ClinicalProtocol,
    ClinicalRecord,
    InteroperabilitySnapshot,
    TranslationResult,
)
from src.interoperability.interoperability_validator import InteroperabilityValidator
from src.io.io_models import IOMessage


class InteroperabilityEngine:
    """
    Unified public façade for Clinical Interoperability.
    """

    def __init__(self) -> None:
        self.fhir_adapter = FHIRAdapter()
        self.hl7_adapter = HL7Adapter()
        self.mapper = ClinicalMapper()
        self.validator = InteroperabilityValidator()
        self._imported_count = 0
        self._exported_count = 0
        self._translated_count = 0
        self._rejected_count = 0
        self._lock = threading.Lock()

    def import_record(
        self,
        raw_data: Any,
        protocol: ClinicalProtocol,
    ) -> Tuple[Optional[ClinicalRecord], TranslationResult]:
        """
        Import a raw FHIR dict or HL7 string into a ClinicalRecord.
        """
        try:
            if protocol == ClinicalProtocol.FHIR:
                if not isinstance(raw_data, dict):
                    raise ValueError("FHIR raw data must be a dictionary.")
                record = self.fhir_adapter.parse_fhir_resource(raw_data)
            elif protocol == ClinicalProtocol.HL7:
                if not isinstance(raw_data, str):
                    raise ValueError("HL7 raw data must be a string.")
                record = self.hl7_adapter.parse_hl7_message(raw_data)
            else:
                raise ValueError(f"Unsupported protocol `{protocol}`.")

            valid, reason = self.validator.validate_record(record)
            if not valid:
                with self._lock:
                    self._rejected_count += 1
                return None, TranslationResult(
                    protocol=protocol,
                    success=False,
                    validation_summary=f"Validation failed: {reason}",
                )

            with self._lock:
                self._imported_count += 1
            return record, TranslationResult(
                protocol=protocol,
                success=True,
                validation_summary="Record valid.",
                translation_notes=f"Successfully imported {record.resource_type.value} record.",
            )

        except Exception as e:
            with self._lock:
                self._rejected_count += 1
            return None, TranslationResult(
                protocol=protocol,
                success=False,
                validation_summary=str(e),
            )

    def import_to_io_message(
        self,
        raw_data: Any,
        protocol: ClinicalProtocol,
        destination: str = "CognitivePipeline",
        session_id: Optional[str] = None,
    ) -> Tuple[Optional[IOMessage], TranslationResult]:
        """
        Import raw FHIR/HL7 data and convert directly into an ingress IOMessage envelope.
        """
        record, res = self.import_record(raw_data, protocol)
        if not res.success or record is None:
            return None, res

        io_msg = self.mapper.record_to_io_message(record, destination=destination, session_id=session_id)
        res.io_message_reference = io_msg.message_id

        with self._lock:
            self._translated_count += 1

        return io_msg, res

    def export_record(
        self,
        io_message: IOMessage,
        target_protocol: ClinicalProtocol,
    ) -> Tuple[Optional[Any], TranslationResult]:
        """
        Convert an outbound IOMessage into a target protocol format (FHIR dict or HL7 string).
        """
        try:
            record = self.mapper.io_message_to_record(io_message, target_protocol=target_protocol)
            valid, reason = self.validator.validate_record(record)
            if not valid:
                with self._lock:
                    self._rejected_count += 1
                return None, TranslationResult(
                    protocol=target_protocol,
                    success=False,
                    validation_summary=f"Export validation failed: {reason}",
                )

            if target_protocol == ClinicalProtocol.FHIR:
                raw_out = self.fhir_adapter.export_fhir_resource(record)
            elif target_protocol == ClinicalProtocol.HL7:
                raw_out = self.hl7_adapter.export_hl7_message(record)
            else:
                raise ValueError(f"Unsupported target protocol `{target_protocol}`.")

            with self._lock:
                self._exported_count += 1
                self._translated_count += 1

            return raw_out, TranslationResult(
                protocol=target_protocol,
                success=True,
                io_message_reference=io_message.message_id,
                validation_summary="Export valid.",
                translation_notes=f"Successfully exported {record.resource_type.value} to {target_protocol.value}.",
            )

        except Exception as e:
            with self._lock:
                self._rejected_count += 1
            return None, TranslationResult(
                protocol=target_protocol,
                success=False,
                validation_summary=str(e),
            )

    def translate(self, record: ClinicalRecord) -> IOMessage:
        return self.mapper.record_to_io_message(record)

    def validate(self, record: ClinicalRecord) -> Tuple[bool, str]:
        return self.validator.validate_record(record)

    def compute_checksum(self) -> str:
        with self._lock:
            data = {
                "imp": self._imported_count,
                "exp": self._exported_count,
                "trans": self._translated_count,
                "rej": self._rejected_count,
            }
            raw = json.dumps(data, sort_keys=True).encode("utf-8")
            return hashlib.sha256(raw).hexdigest()[:16]

    def snapshot(self) -> InteroperabilitySnapshot:
        with self._lock:
            chk = self.compute_checksum()
            return InteroperabilitySnapshot(
                imported_records_count=self._imported_count,
                exported_records_count=self._exported_count,
                translated_count=self._translated_count,
                rejected_count=self._rejected_count,
                checksum=chk,
            )

    def reset(self) -> None:
        with self._lock:
            self.validator.clear()
            self._imported_count = 0
            self._exported_count = 0
            self._translated_count = 0
            self._rejected_count = 0
