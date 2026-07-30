"""
MEMORA Security, Identity & Access Control Data Models.

Defines immutable value objects, enums, identity structures, authorization decisions,
security audit entries, and snapshots.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class IdentityRole(str, Enum):
    PATIENT = "PATIENT"
    CAREGIVER = "CAREGIVER"
    CLINICIAN = "CLINICIAN"
    ADMINISTRATOR = "ADMINISTRATOR"
    SYSTEM = "SYSTEM"


class Permission(str, Enum):
    VIEW_MEMORY = "VIEW_MEMORY"
    MODIFY_CONFIGURATION = "MODIFY_CONFIGURATION"
    START_SESSION = "START_SESSION"
    STOP_SESSION = "STOP_SESSION"
    VIEW_KNOWLEDGE = "VIEW_KNOWLEDGE"
    EXECUTE_REASONING = "EXECUTE_REASONING"
    VIEW_RUNTIME = "VIEW_RUNTIME"
    RUN_INTEGRITY_CHECK = "RUN_INTEGRITY_CHECK"
    EXPORT_AUDIT = "EXPORT_AUDIT"


@dataclass
class Identity:
    """
    Represents an authenticated system or human identity within MEMORA.
    """

    identity_id: str
    display_name: str
    role: IdentityRole
    enabled: bool = True
    permissions: List[Permission] = field(default_factory=list)
    created_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "display_name": self.display_name,
            "role": self.role.value,
            "enabled": self.enabled,
            "permissions": [p.value for p in self.permissions],
            "created_timestamp": self.created_timestamp,
        }


@dataclass
class AuthorizationDecision:
    """
    Represents the result of an authorization evaluation.
    """

    requester: str
    requested_action: str
    granted: bool
    denial_reason: str = ""
    evaluation_time: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requester": self.requester,
            "requested_action": self.requested_action,
            "granted": self.granted,
            "denial_reason": self.denial_reason,
            "evaluation_time": self.evaluation_time,
        }


@dataclass
class SecurityAuditEntry:
    """
    Immutably records a security authorization event.
    """

    identity_id: str
    requested_operation: str
    granted: bool
    denial_reason: str = ""
    entry_id: str = field(default_factory=lambda: f"sec-aud-{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "identity_id": self.identity_id,
            "requested_operation": self.requested_operation,
            "granted": self.granted,
            "denial_reason": self.denial_reason,
            "timestamp": self.timestamp,
        }


@dataclass
class SecuritySnapshot:
    """
    Point-in-time snapshot of registered identities and security states.
    """

    identities_count: int
    active_identities_count: int
    roles_count: int
    checksum: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "identities_count": self.identities_count,
            "active_identities_count": self.active_identities_count,
            "roles_count": self.roles_count,
            "checksum": self.checksum,
        }
