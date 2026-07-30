"""
MEMORA Central Identity Registry.

Manages registered identities, enablement states, role mappings, and security snapshots.
No passwords, network logins, or external authentication protocols are stored.
"""

from __future__ import annotations

import hashlib
import json
import threading
from typing import Dict, List, Optional

from src.security.security_models import Identity, IdentityRole, Permission, SecuritySnapshot


class IdentityRegistry:
    """
    Thread-safe identity registry.
    """

    def __init__(self) -> None:
        self._identities: Dict[str, Identity] = {}
        self._lock = threading.RLock()
        self._seed_default_identities()

    def register_identity(self, identity: Identity) -> None:
        with self._lock:
            self._identities[identity.identity_id] = identity

    def enable_identity(self, identity_id: str) -> None:
        with self._lock:
            if identity_id in self._identities:
                self._identities[identity_id].enabled = True

    def disable_identity(self, identity_id: str) -> None:
        with self._lock:
            if identity_id in self._identities:
                self._identities[identity_id].enabled = False

    def lookup_identity(self, identity_id: str) -> Optional[Identity]:
        with self._lock:
            return self._identities.get(identity_id)

    def list_identities(self) -> List[Identity]:
        with self._lock:
            return list(self._identities.values())

    def compute_checksum(self) -> str:
        with self._lock:
            data = {id_: ident.to_dict() for id_, ident in sorted(self._identities.items())}
            raw = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
            return hashlib.sha256(raw).hexdigest()[:16]

    def snapshot(self) -> SecuritySnapshot:
        with self._lock:
            all_ids = list(self._identities.values())
            active_ids = [i for i in all_ids if i.enabled]
            roles = {i.role for i in all_ids}
            chk = self.compute_checksum()

            return SecuritySnapshot(
                identities_count=len(all_ids),
                active_identities_count=len(active_ids),
                roles_count=len(roles),
                checksum=chk,
            )

    def clear(self) -> None:
        with self._lock:
            self._identities.clear()
            self._seed_default_identities()

    def _seed_default_identities(self) -> None:
        """Seed baseline system identities."""
        defaults = [
            Identity(
                identity_id="id-patient",
                display_name="Margaret (Patient)",
                role=IdentityRole.PATIENT,
                permissions=[Permission.VIEW_MEMORY, Permission.VIEW_KNOWLEDGE],
            ),
            Identity(
                identity_id="id-caregiver",
                display_name="Sarah (Caregiver)",
                role=IdentityRole.CAREGIVER,
                permissions=[
                    Permission.VIEW_MEMORY,
                    Permission.START_SESSION,
                    Permission.STOP_SESSION,
                    Permission.VIEW_KNOWLEDGE,
                ],
            ),
            Identity(
                identity_id="id-clinician",
                display_name="Dr. Smith (Clinician)",
                role=IdentityRole.CLINICIAN,
                permissions=[
                    Permission.VIEW_MEMORY,
                    Permission.VIEW_KNOWLEDGE,
                    Permission.RUN_INTEGRITY_CHECK,
                    Permission.EXPORT_AUDIT,
                    Permission.VIEW_RUNTIME,
                ],
            ),
            Identity(
                identity_id="id-admin",
                display_name="System Administrator",
                role=IdentityRole.ADMINISTRATOR,
                permissions=list(Permission),  # All permissions
            ),
            Identity(
                identity_id="id-system",
                display_name="MEMORA Kernel Daemon",
                role=IdentityRole.SYSTEM,
                permissions=[
                    Permission.EXECUTE_REASONING,
                    Permission.VIEW_RUNTIME,
                    Permission.VIEW_MEMORY,
                    Permission.VIEW_KNOWLEDGE,
                ],
            ),
        ]
        for ident in defaults:
            self._identities[ident.identity_id] = ident
