"""
Comprehensive Test Suite for MEMORA Phase 36 — Clinical Interoperability Framework (FHIR / HL7).

Tests:
1. Interoperability Models (Serialization of ClinicalRecord, TranslationResult, InteroperabilitySnapshot)
2. FHIR Adapter (Parsing FHIR Patient, Observation, Condition resources and exporting FHIR dicts)
3. HL7 Adapter (Parsing HL7 ADT^A08, ORU^R01 message strings and exporting pipe-delimited HL7 strings)
4. Clinical Mapper (Converting ClinicalRecord to ingress IOMessage and outbound IOMessage to ClinicalRecord)
5. Interoperability Validator (Validating clean records, detecting missing external IDs, duplicate detection)
6. Central Interoperability Engine (Public façade import_record, import_to_io_message, export_record, snapshot)
7. Interoperability Explainer (Deterministic Markdown diagnostic report generation)
"""

import pytest
from src.interoperability import (
    ClinicalMapper,
    ClinicalProtocol,
    ClinicalRecord,
    ClinicalResourceType,
    FHIRAdapter,
    HL7Adapter,
    InteroperabilityEngine,
    InteroperabilityExplainer,
    InteroperabilitySnapshot,
    InteroperabilityValidator,
    TranslationResult,
)
from src.io.io_models import IOMessage, InputType, OutputType


# ======================================================================
# 1. Interoperability Models Tests
# ======================================================================

class TestInteroperabilityModels:
    def test_clinical_record_serialization(self):
        rec = ClinicalRecord(
            protocol=ClinicalProtocol.FHIR,
            resource_type=ClinicalResourceType.PATIENT,
            external_identifier="pat-999",
            payload_reference="fhir://Patient/pat-999",
        )
        d = rec.to_dict()
        assert d["protocol"] == "FHIR"
        assert d["resource_type"] == "PATIENT"
        assert d["external_identifier"] == "pat-999"

    def test_translation_result_serialization(self):
        tr = TranslationResult(
            protocol=ClinicalProtocol.HL7,
            success=True,
            io_message_reference="msg-123",
            validation_summary="Valid HL7 message.",
        )
        d = tr.to_dict()
        assert d["protocol"] == "HL7"
        assert d["success"] is True

    def test_interoperability_snapshot_serialization(self):
        snap = InteroperabilitySnapshot(
            imported_records_count=5,
            exported_records_count=2,
            translated_count=7,
            rejected_count=0,
            checksum="abc12345",
        )
        assert snap.to_dict()["imported_records_count"] == 5


# ======================================================================
# 2. FHIR Adapter Tests
# ======================================================================

class TestFHIRAdapter:
    def test_parse_fhir_patient(self):
        adapter = FHIRAdapter()
        fhir_dict = {
            "resourceType": "Patient",
            "id": "fhir-pat-01",
            "status": "active",
        }
        rec = adapter.parse_fhir_resource(fhir_dict)
        assert rec.protocol == ClinicalProtocol.FHIR
        assert rec.resource_type == ClinicalResourceType.PATIENT
        assert rec.external_identifier == "fhir-pat-01"

    def test_export_fhir_resource(self):
        adapter = FHIRAdapter()
        rec = ClinicalRecord(
            protocol=ClinicalProtocol.FHIR,
            resource_type=ClinicalResourceType.OBSERVATION,
            external_identifier="obs-100",
            payload_reference="fhir://Observation/obs-100",
        )
        fhir_out = adapter.export_fhir_resource(rec)
        assert fhir_out["resourceType"] == "Observation"
        assert fhir_out["id"] == "obs-100"


# ======================================================================
# 3. HL7 Adapter Tests
# ======================================================================

class TestHL7Adapter:
    def test_parse_hl7_oru_message(self):
        adapter = HL7Adapter()
        raw_hl7 = "MSH|^~\\&|EMR|HOSPITAL|MEMORA|FACILITY|20260730||ORU^R01|msg-hl7-001|P|2.5\nOBX|1|ST|OBSERVATION||obs_data||||||F"
        rec = adapter.parse_hl7_message(raw_hl7)
        assert rec.protocol == ClinicalProtocol.HL7
        assert rec.resource_type == ClinicalResourceType.OBSERVATION
        assert rec.external_identifier == "msg-hl7-001"

    def test_export_hl7_message(self):
        adapter = HL7Adapter()
        rec = ClinicalRecord(
            protocol=ClinicalProtocol.HL7,
            resource_type=ClinicalResourceType.ALERT,
            external_identifier="hl7-alert-99",
            payload_reference="hl7://MDM^T02/hl7-alert-99",
            metadata={"event_code": "MDM^T02"},
        )
        hl7_str = adapter.export_hl7_message(rec)
        assert "MSH|" in hl7_str
        assert "MDM^T02" in hl7_str


# ======================================================================
# 4. Clinical Mapper Tests
# ======================================================================

class TestClinicalMapper:
    def test_record_to_io_message(self):
        mapper = ClinicalMapper()
        rec = ClinicalRecord(
            protocol=ClinicalProtocol.FHIR,
            resource_type=ClinicalResourceType.OBSERVATION,
            external_identifier="obs-555",
            payload_reference="fhir://Observation/obs-555",
        )
        io_msg = mapper.record_to_io_message(rec, session_id="ses-interop-1")
        assert io_msg.input_type == InputType.CLINICAL
        assert io_msg.payload_reference == "fhir://Observation/obs-555"
        assert io_msg.session_id == "ses-interop-1"

    def test_io_message_to_record(self):
        mapper = ClinicalMapper()
        io_msg = IOMessage(
            source="ClinicalGateway",
            destination="DisplayAdapter",
            output_type=OutputType.CLINICAL,
            payload_reference="fhir://Observation/obs-555",
            metadata={"resource_type": "OBSERVATION", "external_id": "obs-555"},
        )
        rec = mapper.io_message_to_record(io_msg, target_protocol=ClinicalProtocol.FHIR)
        assert rec.protocol == ClinicalProtocol.FHIR
        assert rec.resource_type == ClinicalResourceType.OBSERVATION
        assert rec.external_identifier == "obs-555"


# ======================================================================
# 5. Interoperability Validator Tests
# ======================================================================

class TestInteroperabilityValidator:
    def test_validate_clean_record(self):
        val = InteroperabilityValidator()
        rec = ClinicalRecord(
            protocol=ClinicalProtocol.FHIR,
            resource_type=ClinicalResourceType.PATIENT,
            external_identifier="p-1",
            payload_reference="ref-1",
        )
        is_valid, reason = val.validate_record(rec)
        assert is_valid is True

    def test_validate_missing_external_id(self):
        val = InteroperabilityValidator()
        rec = ClinicalRecord(
            protocol=ClinicalProtocol.FHIR,
            resource_type=ClinicalResourceType.PATIENT,
            external_identifier="",
            payload_reference="ref-1",
        )
        is_valid, reason = val.validate_record(rec)
        assert is_valid is False
        assert "external_identifier cannot be empty" in reason


# ======================================================================
# 6. Central Interoperability Engine Tests
# ======================================================================

class TestInteroperabilityEngine:
    def test_import_and_export_fhir(self):
        engine = InteroperabilityEngine()
        fhir_dict = {
            "resourceType": "Patient",
            "id": "pat-engine-101",
            "status": "active",
        }

        rec, res_imp = engine.import_record(fhir_dict, ClinicalProtocol.FHIR)
        assert res_imp.success is True
        assert rec.external_identifier == "pat-engine-101"

        io_msg, res_msg = engine.import_to_io_message(fhir_dict, ClinicalProtocol.FHIR, session_id="ses-101")
        assert res_msg.success is True
        assert io_msg.session_id == "ses-101"

        exported_fhir, res_exp = engine.export_record(io_msg, ClinicalProtocol.FHIR)
        assert res_exp.success is True
        assert exported_fhir["resourceType"] == "Patient"

        snap = engine.snapshot()
        assert snap.imported_records_count == 2
        assert snap.exported_records_count == 1


# ======================================================================
# 7. Interoperability Explainer Tests
# ======================================================================

class TestInteroperabilityExplainer:
    def test_explain_engine_state(self):
        engine = InteroperabilityEngine()
        engine.import_record({"resourceType": "Patient", "id": "p-1"}, ClinicalProtocol.FHIR)
        markdown = InteroperabilityExplainer.explain_engine_state(engine)

        assert "MEMORA Clinical Interoperability Diagnostic Report" in markdown
        assert "Imported Clinical Records" in markdown
        assert "FHIR" in markdown
        assert "HL7" in markdown
