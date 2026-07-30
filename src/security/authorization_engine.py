"""
MEMORA Deterministic Authorization Engine.

Evaluates permission requests against Identity roles and granted permission lists.
Operates deterministically without external policy scripts or probabilistic logic.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from src.security.security_models import AuthorizationDecision, Identity, IdentityRole, Permission


# Default role permission matrix
ROLE_PERMISSIONS: Dict[IdentityRole, Set[Permission]] = {
    IdentityRole.PATIENT: {
        Permission.VIEW_MEMORY,
        Permission.VIEW_KNOWLEDGE,
    },
    IdentityRole.CAREGIVER: {
        Permission.VIEW_MEMORY,
        Permission.VIEW_KNOWLEDGE,
        Permission.START_SESSION,
        Permission.STOP_SESSION,
    },
    IdentityRole.CLINICIAN: {
        Permission.VIEW_MEMORY,
        Permission.VIEW_KNOWLEDGE,
        Permission.RUN_INTEGRITY_CHECK,
        Permission.EXPORT_AUDIT,
        Permission.VIEW_RUNTIME,
    },
    IdentityRole.ADMINISTRATOR: set(Permission),  # All permissions
    IdentityRole.SYSTEM: {
        Permission.EXECUTE_REASONING,
        Permission.VIEW_RUNTIME,
        Permission.VIEW_MEMORY,
        Permission.VIEW_KNOWLEDGE,
    },
}


class AuthorizationEngine:
    """
    Deterministic permission evaluation engine.
    """

    @classmethod
    def evaluate(cls, identity: Optional[Identity], permission: Permission) -> AuthorizationDecision:
        requester_id = identity.identity_id if identity else "anonymous"
        action_name = permission.value

        # 1. Identity existence check
        if identity is None:
            return AuthorizationDecision(
                requester=requester_id,
                requested_action=action_name,
                granted=False,
                denial_reason="Identity is null or unauthenticated.",
            )

        # 2. Identity enablement check
        if not identity.enabled:
            return AuthorizationDecision(
                requester=requester_id,
                requested_action=action_name,
                granted=False,
                denial_reason=f"Identity '{identity.identity_id}' is disabled.",
            )

        # 3. Explicit identity permissions check
        if permission in identity.permissions:
            return AuthorizationDecision(
                requester=requester_id,
                requested_action=action_name,
                granted=True,
                denial_reason="",
            )

        # 4. Role default permission matrix check
        default_role_perms = ROLE_PERMISSIONS.get(identity.role, set())
        if permission in default_role_perms:
            return AuthorizationDecision(
                requester=requester_id,
                requested_action=action_name,
                granted=True,
                denial_reason="",
            )

        # 5. Permission denied fallback
        return AuthorizationDecision(
            requester=requester_id,
            requested_action=action_name,
            granted=False,
            denial_reason=f"Role '{identity.role.value}' lacks permission '{action_name}'.",
        )
