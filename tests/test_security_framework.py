"""
Comprehensive Test Suite for MEMORA Phase 34 — Security, Identity & Access Control Framework.

Tests:
1. Security Data Models (Serialization of Identity, AuthorizationDecision, SecurityAuditEntry, SecuritySnapshot)
2. Identity Registry (Identity registration, lookup, enable/disable toggle, snapshotting, checksum)
3. Authorization Engine (Role permission evaluation, explicit permission override, disabled identity rejection)
4. Access Controller (Operation permission checks: can_start_session, can_modify_configuration, etc.)
5. Security Audit Logger (Audit logging, denied audit retrieval)
6. Central Security Engine (Unified authorization façade, snapshotting, audit tracking)
7. Security Explainer (Deterministic Markdown diagnostic report generation)
"""

import pytest
from src.security import (
    AccessController,
    AuditSecurity,
    AuthorizationDecision,
    AuthorizationEngine,
    Identity,
    IdentityRegistry,
    IdentityRole,
    Permission,
    SecurityAuditEntry,
    SecurityEngine,
    SecurityExplainer,
    SecuritySnapshot,
)


# ======================================================================
# 1. Security Data Models Tests
# ======================================================================

class TestSecurityModels:
    def test_identity_serialization(self):
        ident = Identity(
            identity_id="id-test",
            display_name="Test User",
            role=IdentityRole.CAREGIVER,
            permissions=[Permission.VIEW_MEMORY],
        )
        d = ident.to_dict()
        assert d["identity_id"] == "id-test"
        assert d["role"] == "CAREGIVER"
        assert "VIEW_MEMORY" in d["permissions"]

    def test_authorization_decision_serialization(self):
        dec = AuthorizationDecision(
            requester="id-patient",
            requested_action="VIEW_MEMORY",
            granted=True,
        )
        d = dec.to_dict()
        assert d["requester"] == "id-patient"
        assert d["granted"] is True

    def test_security_snapshot_serialization(self):
        snap = SecuritySnapshot(
            identities_count=5,
            active_identities_count=5,
            roles_count=5,
            checksum="abc12345",
        )
        assert snap.to_dict()["identities_count"] == 5


# ======================================================================
# 2. Identity Registry Tests
# ======================================================================

class TestIdentityRegistry:
    def test_registry_registration_and_lookup(self):
        reg = IdentityRegistry()
        ident = Identity("id-user1", "User One", IdentityRole.CLINICIAN)
        reg.register_identity(ident)

        found = reg.lookup_identity("id-user1")
        assert found is not None
        assert found.role == IdentityRole.CLINICIAN

    def test_enable_disable_identity(self):
        reg = IdentityRegistry()
        reg.disable_identity("id-patient")
        ident = reg.lookup_identity("id-patient")
        assert ident.enabled is False

        reg.enable_identity("id-patient")
        assert ident.enabled is True

    def test_snapshot_computation(self):
        reg = IdentityRegistry()
        snap = reg.snapshot()
        assert snap.identities_count >= 5  # Baseline defaults seeded


# ======================================================================
# 3. Authorization Engine Tests
# ======================================================================

class TestAuthorizationEngine:
    def test_role_based_permissions(self):
        reg = IdentityRegistry()
        patient = reg.lookup_identity("id-patient")
        admin = reg.lookup_identity("id-admin")

        # Patient cannot modify config
        dec1 = AuthorizationEngine.evaluate(patient, Permission.MODIFY_CONFIGURATION)
        assert dec1.granted is False

        # Admin can modify config
        dec2 = AuthorizationEngine.evaluate(admin, Permission.MODIFY_CONFIGURATION)
        assert dec2.granted is True

    def test_disabled_identity_rejection(self):
        ident = Identity("id-disabled", "Disabled User", IdentityRole.ADMINISTRATOR, enabled=False)
        dec = AuthorizationEngine.evaluate(ident, Permission.VIEW_MEMORY)
        assert dec.granted is False
        assert "disabled" in dec.denial_reason


# ======================================================================
# 4. Access Controller Tests
# ======================================================================

class TestAccessController:
    def test_access_controller_facade(self):
        ac = AccessController()
        reg = IdentityRegistry()
        caregiver = reg.lookup_identity("id-caregiver")
        patient = reg.lookup_identity("id-patient")

        assert ac.can_start_session(caregiver).granted is True
        assert ac.can_modify_configuration(patient).granted is False
        assert ac.can_run_integrity(reg.lookup_identity("id-clinician")).granted is True


# ======================================================================
# 5. Security Audit Logger Tests
# ======================================================================

class TestAuditSecurity:
    def test_audit_logging(self):
        audit = AuditSecurity()
        audit.record_audit("id-patient", "MODIFY_CONFIGURATION", False, "Role lacks permission")
        assert len(audit.get_entries()) == 1
        assert len(audit.get_denied_entries()) == 1


# ======================================================================
# 6. Central Security Engine Tests
# ======================================================================

class TestSecurityEngine:
    def test_engine_authorize_and_audit(self):
        engine = SecurityEngine()
        dec = engine.authorize("id-caregiver", Permission.START_SESSION)
        assert dec.granted is True

        logs = engine.audit_log()
        assert len(logs) == 1
        assert logs[0].requested_operation == "START_SESSION"

    def test_engine_register_and_list(self):
        engine = SecurityEngine()
        new_id = Identity("id-nurse", "Nurse Mary", IdentityRole.CLINICIAN)
        engine.register_identity(new_id)

        assert engine.lookup_identity("id-nurse") is not None
        assert len(engine.list_identities()) >= 6


# ======================================================================
# 7. Security Explainer Tests
# ======================================================================

class TestSecurityExplainer:
    def test_explain_security_state(self):
        engine = SecurityEngine()
        engine.authorize("id-patient", Permission.MODIFY_CONFIGURATION)  # Denied request
        markdown = SecurityExplainer.explain_security_state(engine)

        assert "MEMORA Security, Identity & Access Control Diagnostic Report" in markdown
        assert "id-patient" in markdown
        assert "Denied Access Request Details" in markdown
