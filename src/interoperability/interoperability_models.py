"""
MEMORA Clinical Interoperability Framework Data Models.

Defines immutable value objects, clinical protocol schemas, resource classifications,
translation results, and snapshot structures.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ClinicalProtocol(str, Enum):
    """
    Supported healthcare interoperability message protocols.
    """

    FHIR = "FHIR"
    HL7 = "HL7"


class ClinicalResourceType(str, Enum):
    """
    Supported clinical resource classifications.
    """

    PATIENT = "PATIENT"
    OBSERVATION = "OBSERVATION"
    CONDITION = "CONDITION"
    MEDICATION = "MEDICATION"
    ENCOUNTER = "ENCOUNTER"
    DEVICE = "DEVICE"
    CARE_PLAN = "CARE_PLAN"
    ALERT = "ALERT"


@dataclass
class ClinicalRecord:
    """
    Standardized payload-neutral clinical record representation.
    """

    protocol: ClinicalProtocol
    resource_type: ClinicalResourceType
    external_identifier: str
    payload_reference: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    record_id: str = field(default_factory=lambda: f"rec-{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize ClinicalRecord to a dictionary representation."""
        return {
            "record_id": self.record_id,
            "protocol": self.protocol.value,
            "resource_type": self.resource_type.value,
            "external_identifier": self.external_identifier,
            "payload_reference": self.payload_reference,
            "metadata": dict(self.metadata),
            "timestamp": self.timestamp,
        }


@dataclass
class TranslationResult:
    """
    Represents the result of a clinical translation cycle.
    """

    protocol: ClinicalProtocol
    success: bool
    io_message_reference: str = ""
    validation_summary: str = ""
    translation_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize TranslationResult to a dictionary representation."""
        return {
            "protocol": self.protocol.value,
            "success": self.success,
            "io_message_reference": self.io_message_reference,
            "validation_summary": self.validation_summary,
            "translation_notes": self.translation_notes,
        }


@dataclass
class InteroperabilitySnapshot:
    """
    Point-in-time snapshot of clinical record translation activity and checksum.
    """

    imported_records_count: int
    exported_records_count: int
    translated_count: int
    rejected_count: int
    checksum: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize InteroperabilitySnapshot to a dictionary representation."""
        return {
            "timestamp": self.timestamp,
            "imported_records_count": self.imported_records_count,
            "exported_records_count": self.exported_records_count,
            "translated_count": self.translated_count,
            "rejected_count": self.rejected_count,
            "checksum": self.checksum,
        }
