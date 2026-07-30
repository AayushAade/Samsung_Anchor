"""
MEMORA Central Security Engine.

Public façade coordinating IdentityRegistry, AuthorizationEngine, AccessController,
and AuditSecurity. Serves as the single security authority for permission decisions.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from src.security.access_controller import AccessController
from src.security.audit_security import AuditSecurity
from src.security.authorization_engine import AuthorizationEngine
from src.security.identity_registry import IdentityRegistry
from src.security.security_models import (
    AuthorizationDecision,
    Identity,
    Permission,
    SecurityAuditEntry,
    SecuritySnapshot,
)


class SecurityEngine:
    """
    Unified public façade for Security, Identity & Access Control.
    """

    def __init__(self) -> None:
        self.identity_registry = IdentityRegistry()
        self.auth_engine = AuthorizationEngine()
        self.access_controller = AccessController(self.auth_engine)
        self.audit_security = AuditSecurity()
        self._lock = threading.Lock()

    def authorize(self, identity_id: str, permission: Permission) -> AuthorizationDecision:
        identity = self.identity_registry.lookup_identity(identity_id)
        decision = self.auth_engine.evaluate(identity, permission)

        # Record security audit entry
        self.audit_security.record_audit(
            identity_id=identity_id,
            requested_operation=permission.value,
            granted=decision.granted,
            denial_reason=decision.denial_reason,
        )

        return decision

    def register_identity(self, identity: Identity) -> None:
        self.identity_registry.register_identity(identity)

    def enable_identity(self, identity_id: str) -> None:
        self.identity_registry.enable_identity(identity_id)

    def disable_identity(self, identity_id: str) -> None:
        self.identity_registry.disable_identity(identity_id)

    def lookup_identity(self, identity_id: str) -> Optional[Identity]:
        return self.identity_registry.lookup_identity(identity_id)

    def list_identities(self) -> List[Identity]:
        return self.identity_registry.list_identities()

    def snapshot(self) -> SecuritySnapshot:
        return self.identity_registry.snapshot()

    def audit_log(self) -> List[SecurityAuditEntry]:
        return self.audit_security.get_entries()

    def reset(self) -> None:
        with self._lock:
            self.identity_registry.clear()
            self.audit_security.clear()
