"""
Comprehensive Test Suite for MEMORA Phase 22 — Trust, Safety, Reliability & Deployment Framework.

Tests all 9 Phase 22 modules:
1. Unified Safety Manager & 6 Guardrail Rules
2. Evidence Accumulator & Temporal Decay Pools
3. Audit Framework & Privacy-Conscious Export
4. Caregiver Config Manager & Preference Validation
5. Privacy Manager & Data Lifecycle Retention Purge
6. Degradation Manager & Graceful Failure Recovery
7. Deployment Validator & Pre-Flight Diagnostics
8. Pipeline Integration & Safety Enforcement
"""

import os
import tempfile
import time
import pytest
from datetime import datetime

from src.cognition.cos.models import CognitiveAction, CognitiveActionType
from src.cognition.context.models import CognitiveContext, IdentityContext
from src.cognition.goals.models import GoalHypothesis, GoalCategory, GoalState, EvidenceSignal
from src.clinical.patient_state import PatientState, PatientStateMode
from src.trust.models import (
    SafetyStatus,
    EvidenceType,
    AuditExportFormat,
    DataCategory,
    SubsystemHealthState,
)
from src.trust.safety_manager import SafetyManager
from src.trust.evidence_accumulator import EvidenceAccumulator
from src.trust.audit_framework import AuditFramework
from src.trust.caregiver_config import CaregiverConfigManager, CaregiverPreferences
from src.trust.privacy_manager import PrivacyManager
from src.trust.degradation_manager import DegradationManager
from deployment.validation.deployment_validator import DeploymentValidator


# ======================================================================
# 1. Safety Guardrails & Safety Manager Tests
# ======================================================================

class TestSafetyManager:
    def test_approved_action(self):
        mgr = SafetyManager(min_confidence_threshold=0.35, quiet_hours_start=0, quiet_hours_end=0)
        action = CognitiveAction(action_type=CognitiveActionType.SPEAK, reasoning_path="Reasoning ok", confidence=0.85)
        ps = PatientState(mode=PatientStateMode.CALM, confidence=0.9, primary_need="Routine support")
        
        eval_result = mgr.evaluate_action(action=action, patient_state=ps)
        assert eval_result.status == SafetyStatus.APPROVED
        assert eval_result.final_action.action_type == CognitiveActionType.SPEAK
        assert len(eval_result.check_results) == 6

    def test_confidence_threshold_downgrade(self):
        mgr = SafetyManager(min_confidence_threshold=0.50, quiet_hours_start=0, quiet_hours_end=0)
        action = CognitiveAction(action_type=CognitiveActionType.SPEAK, reasoning_path="Low conf action", confidence=0.30)
        
        eval_result = mgr.evaluate_action(action=action)
        assert eval_result.status == SafetyStatus.DOWNGRADED
        assert eval_result.final_action.action_type == CognitiveActionType.REMAIN_SILENT

    def test_identity_consistency_check(self):
        mgr = SafetyManager(quiet_hours_start=0, quiet_hours_end=0)
        action = CognitiveAction(action_type=CognitiveActionType.SPEAK, reasoning_path="Check identity", confidence=0.80)
        ctx = CognitiveContext(
            timestamp=datetime.now(),
            identity=IdentityContext(face_id="f1", name="Sarah", relationship="Daughter", confidence=0.10, is_known=True),
            memory=None,
            temporal=None,
        )
        
        eval_result = mgr.evaluate_action(action=action, context=ctx)
        assert eval_result.status == SafetyStatus.DOWNGRADED
        assert eval_result.final_action.action_type == CognitiveActionType.REMAIN_SILENT

    def test_working_memory_freshness_check(self):
        mgr = SafetyManager(quiet_hours_start=0, quiet_hours_end=0)
        action = CognitiveAction(action_type=CognitiveActionType.SPEAK, reasoning_path="Check WM", confidence=0.80, metadata={"working_memory_key": "stale_slot"})
        wm_snapshot = {
            "slots": {
                "stale_slot": {"key": "stale_slot", "is_expired": True}
            }
        }
        
        eval_result = mgr.evaluate_action(action=action, working_memory_snapshot=wm_snapshot)
        assert eval_result.status == SafetyStatus.DOWNGRADED
        assert eval_result.final_action.action_type == CognitiveActionType.REMAIN_SILENT

    def test_reminder_frequency_throttling(self):
        mgr = SafetyManager(reminder_throttle_seconds=3600.0, quiet_hours_start=0, quiet_hours_end=0)
        action = CognitiveAction(action_type=CognitiveActionType.SPEAK, reasoning_path="Med reminder", confidence=0.85, metadata={"goal": "Medication Routine"})
        
        # First call passes and records timestamp
        res1 = mgr.evaluate_action(action=action)
        assert res1.status == SafetyStatus.APPROVED
        
        # Immediate second call is throttled
        res2 = mgr.evaluate_action(action=action)
        assert res2.status in (SafetyStatus.BLOCKED, SafetyStatus.DOWNGRADED)
        assert res2.final_action.action_type == CognitiveActionType.REMAIN_SILENT

    def test_evidence_consistency_check(self):
        mgr = SafetyManager(quiet_hours_start=0, quiet_hours_end=0)
        action = CognitiveAction(action_type=CognitiveActionType.SPEAK, reasoning_path="Evidence check", confidence=0.85)
        goal = GoalHypothesis(
            name="Medication",
            category=GoalCategory.MEDICAL,
            confidence=0.4,
            supporting_evidence=[EvidenceSignal(source="S", signal="sig", weight=0.1, timestamp=datetime.now())],
            contradicting_evidence=[EvidenceSignal(source="S", signal="sig", weight=0.8, timestamp=datetime.now())],
        )
        
        eval_result = mgr.evaluate_action(action=action, goals=[goal])
        assert eval_result.status == SafetyStatus.DOWNGRADED
        assert eval_result.final_action.action_type == CognitiveActionType.REMAIN_SILENT

    def test_quiet_hours_check(self):
        cur_hour = datetime.now().hour
        # Set quiet hours to include current hour
        mgr = SafetyManager(quiet_hours_start=cur_hour, quiet_hours_end=(cur_hour + 1) % 24)
        action = CognitiveAction(action_type=CognitiveActionType.SPEAK, reasoning_path="Quiet test", confidence=0.85)
        
        eval_result = mgr.evaluate_action(action=action)
        assert eval_result.status == SafetyStatus.MODIFIED
        assert eval_result.final_action.action_type == CognitiveActionType.REMAIN_SILENT

    def test_emergency_override(self):
        mgr = SafetyManager(quiet_hours_start=0, quiet_hours_end=0)
        action = CognitiveAction(action_type=CognitiveActionType.ESCALATE_TO_CAREGIVER, reasoning_path="Emerg action", confidence=1.0)
        ps = PatientState(mode=PatientStateMode.EMERGENCY, confidence=1.0, primary_need="Fall safety")
        
        eval_result = mgr.evaluate_action(action=action, patient_state=ps)
        assert eval_result.status == SafetyStatus.ESCALATED
        assert eval_result.final_action.action_type == CognitiveActionType.ESCALATE_TO_CAREGIVER


# ======================================================================
# 2. Evidence Accumulation Tests
# ======================================================================

class TestEvidenceAccumulator:
    def test_record_and_summary(self):
        acc = EvidenceAccumulator(decay_halflife_seconds=600.0)
        acc.record_evidence("identity:Sarah", EvidenceType.FACE_OBSERVATION, "FaceRecognizer", "matched_face", "Sarah", weight=0.5)
        acc.record_evidence("identity:Sarah", EvidenceType.FACE_OBSERVATION, "FaceRecognizer", "matched_face", "Sarah", weight=0.4)
        
        summary = acc.get_summary("identity:Sarah")
        assert summary.supporting_count == 2
        assert summary.contradicting_count == 0
        assert summary.accumulated_confidence > 0.40
        assert summary.is_conflicted is False

    def test_conflict_detection(self):
        acc = EvidenceAccumulator()
        acc.record_evidence("identity:Unknown", EvidenceType.FACE_OBSERVATION, "FaceRec", "sig", "Sarah", weight=0.3)
        acc.record_evidence("identity:Unknown", EvidenceType.FACE_OBSERVATION, "FaceRec", "sig", "Riya", weight=-0.6)
        
        summary = acc.get_summary("identity:Unknown")
        assert summary.is_conflicted is True
        assert "Conflicting evidence" in summary.explanation

    def test_purge_decayed_evidence(self):
        acc = EvidenceAccumulator()
        acc.record_evidence("k1", EvidenceType.TEMPORAL_SIGNAL, "Temporal", "t", "v")
        # Purge with negative max age to evict everything
        purged = acc.purge_decayed_evidence(max_age_seconds=-1.0)
        assert purged == 1
        assert acc.get_summary("k1").supporting_count == 0


# ======================================================================
# 3. Audit Framework Tests
# ======================================================================

class TestAuditFramework:
    def test_record_audit(self):
        fw = AuditFramework(redact_pii_by_default=True)
        rec = fw.record_audit(
            cycle_id=10,
            triggering_event="PERSON_ARRIVED",
            active_goal="Medication Routine",
            active_context_summary="Context with Eleanor present",
            working_memory_keys=["current_visitor"],
            selected_care_policy="Validation Therapy",
            evidence_summary="Safety: APPROVED",
            safety_status="APPROVED",
            safety_checks_passed=6,
            safety_checks_failed=[],
            proposed_action="SPEAK",
            final_action="SPEAK",
            explanation="Safety passed",
            patient_name="Eleanor",
        )
        assert rec.audit_id.startswith("aud-")
        assert "Eleanor" not in rec.active_context_summary  # Redacted
        assert "Subject#" in rec.active_context_summary

    def test_export_formats(self):
        fw = AuditFramework(redact_pii_by_default=False)
        fw.record_audit(1, "E", "G", "C", [], "P", "S", "APPROVED", 6, [], "SPEAK", "SPEAK", "Expl")
        
        json_out = fw.export_records(AuditExportFormat.JSON)
        assert "cycle_id" in json_out
        
        csv_out = fw.export_records(AuditExportFormat.CSV)
        assert "audit_id,timestamp,cycle_id" in csv_out


# ======================================================================
# 4. Caregiver Config Manager Tests
# ======================================================================

class TestCaregiverConfigManager:
    def test_default_preferences_validation(self):
        prefs = CaregiverPreferences()
        errors = prefs.validate()
        assert len(errors) == 0

    def test_preference_update_validation(self):
        mgr = CaregiverConfigManager(config_path="nonexistent_config.json")
        errs = mgr.update({"min_confidence_threshold": 0.50, "speech_verbosity": "DETAILED"})
        assert len(errs) == 0
        assert mgr.get_preferences().min_confidence_threshold == 0.50

    def test_invalid_preference_rejection(self):
        mgr = CaregiverConfigManager(config_path="nonexistent_config.json")
        errs = mgr.update({"min_confidence_threshold": 1.50})  # Invalid threshold
        assert len(errs) > 0


# ======================================================================
# 5. Privacy Manager Tests
# ======================================================================

class TestPrivacyManager:
    def test_retention_policy_classification(self):
        pm = PrivacyManager()
        pol = pm.get_policy(DataCategory.TRANSIENT_WORKING_MEMORY)
        assert pol.retention_period_seconds == 300.0
        assert pol.auto_purge_enabled is True

    def test_purge_expired_records(self):
        pm = PrivacyManager()
        acc = EvidenceAccumulator()
        acc.record_evidence("k1", EvidenceType.TEMPORAL_SIGNAL, "Temporal", "t", "v")
        
        # Purge
        res = pm.purge_expired_records(evidence_accumulator=acc)
        assert "evidence_records" in res

    def test_secure_delete_patient_data(self):
        pm = PrivacyManager()
        fw = AuditFramework()
        fw.record_audit(1, "E", "G", "C", [], "P", "S", "APPROVED", 6, [], "SPEAK", "SPEAK", "Expl")
        
        deleted = pm.secure_delete_patient_data(audit_framework=fw)
        assert deleted is True
        assert len(fw.get_recent_records()) == 0


# ======================================================================
# 6. Failure Recovery & Degradation Manager Tests
# ======================================================================

class TestDegradationManager:
    def test_report_hardware_failure(self):
        dm = DegradationManager()
        status = dm.report_hardware_failure("camera", "Device disconnected")
        assert status.camera_state == SubsystemHealthState.UNAVAILABLE
        assert status.overall_health == "DEGRADED"
        assert len(status.active_fallbacks) == 1

    def test_component_recovery(self):
        dm = DegradationManager()
        dm.report_hardware_failure("camera", "Device disconnected")
        status = dm.recover_hardware("camera")
        assert status.camera_state == SubsystemHealthState.FULL
        assert status.overall_health == "HEALTHY"


# ======================================================================
# 7. Deployment Validator Tests
# ======================================================================

class TestDeploymentValidator:
    def test_run_diagnostics(self):
        val = DeploymentValidator()
        report = val.run_diagnostics()
        assert report.total_checks >= 5
        assert report.passed_checks > 0
        assert report.is_deployment_ready is True
        
        md = report.generate_markdown()
        assert "MEMORA Pre-Flight Deployment Readiness Report" in md
        assert "OperatingSystemCheck" in md


# ======================================================================
# 8. Pipeline Integration Tests
# ======================================================================

class TestPipelineTrustIntegration:
    def test_pipeline_instantiates_trust_modules(self):
        from src.memory.database import MemoraDatabase
        from src.pipeline.cognitive_pipeline import CognitivePipeline
        
        db = MemoraDatabase(db_path=os.path.join(tempfile.gettempdir(), "test_trust_pipeline.sqlite"))
        db.clear()
        pipeline = CognitivePipeline(database=db)
        
        assert hasattr(pipeline, "safety_manager")
        assert hasattr(pipeline, "evidence_accumulator")
        assert hasattr(pipeline, "audit_framework")
        assert hasattr(pipeline, "privacy_manager")
        assert hasattr(pipeline, "degradation_manager")
        
        # Execute one cognitive cycle
        actions = pipeline.process({"face_id": "face_sarah", "name": "Sarah", "relationship": "Daughter"})
        assert pipeline.latest_audit_record is not None
        assert pipeline.latest_audit_record.safety_status in ("APPROVED", "MODIFIED", "DOWNGRADED", "ESCALATED")
