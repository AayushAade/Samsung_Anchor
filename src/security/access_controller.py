"""
MEMORA High-Level Access Controller.

Validates operational permission boundaries across pipeline and subsystem operations.
Never invokes underlying subsystem logic; produces authorization decisions only.
"""

from __future__ import annotations

from typing import Optional

from src.security.authorization_engine import AuthorizationEngine
from src.security.security_models import AuthorizationDecision, Identity, Permission


class AccessController:
    """
    Subsystem access validation façade.
    """

    def __init__(self, auth_engine: Optional[AuthorizationEngine] = None) -> None:
        self.auth_engine = auth_engine or AuthorizationEngine()

    def can_start_session(self, identity: Optional[Identity]) -> AuthorizationDecision:
        return self.auth_engine.evaluate(identity, Permission.START_SESSION)

    def can_stop_session(self, identity: Optional[Identity]) -> AuthorizationDecision:
        return self.auth_engine.evaluate(identity, Permission.STOP_SESSION)

    def can_modify_configuration(self, identity: Optional[Identity]) -> AuthorizationDecision:
        return self.auth_engine.evaluate(identity, Permission.MODIFY_CONFIGURATION)

    def can_run_integrity(self, identity: Optional[Identity]) -> AuthorizationDecision:
        return self.auth_engine.evaluate(identity, Permission.RUN_INTEGRITY_CHECK)

    def can_export_audit(self, identity: Optional[Identity]) -> AuthorizationDecision:
        return self.auth_engine.evaluate(identity, Permission.EXPORT_AUDIT)

    def can_access_memory(self, identity: Optional[Identity]) -> AuthorizationDecision:
        return self.auth_engine.evaluate(identity, Permission.VIEW_MEMORY)

    def can_access_knowledge(self, identity: Optional[Identity]) -> AuthorizationDecision:
        return self.auth_engine.evaluate(identity, Permission.VIEW_KNOWLEDGE)

    def can_execute_reasoning(self, identity: Optional[Identity]) -> AuthorizationDecision:
        return self.auth_engine.evaluate(identity, Permission.EXECUTE_REASONING)

    def can_view_runtime(self, identity: Optional[Identity]) -> AuthorizationDecision:
        return self.auth_engine.evaluate(identity, Permission.VIEW_RUNTIME)
