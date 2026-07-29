"""
MEMORA Privacy & Data Lifecycle — Privacy Manager.

Classifies and enforces data retention policies across transient working memory,
operational logs, audit records, caregiver reports, and long-term memory.
Provides automated data purging and secure patient data deletion.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from src.trust.models import DataCategory, RetentionPolicy


class PrivacyManager:
    """
    Manages privacy classifications, retention schedules, and automated data purging.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # Default Retention Schedules (seconds)
        self._policies: Dict[DataCategory, RetentionPolicy] = {
            DataCategory.TRANSIENT_WORKING_MEMORY: RetentionPolicy(
                category=DataCategory.TRANSIENT_WORKING_MEMORY,
                retention_period_seconds=300.0,  # 5 minutes
                auto_purge_enabled=True,
                encrypt_at_rest=False,
                pii_redaction_required=False,
            ),
            DataCategory.OPERATIONAL_LOGS: RetentionPolicy(
                category=DataCategory.OPERATIONAL_LOGS,
                retention_period_seconds=7 * 86400.0,  # 7 days
                auto_purge_enabled=True,
                encrypt_at_rest=True,
                pii_redaction_required=True,
            ),
            DataCategory.AUDIT_RECORDS: RetentionPolicy(
                category=DataCategory.AUDIT_RECORDS,
                retention_period_seconds=30 * 86400.0,  # 30 days
                auto_purge_enabled=True,
                encrypt_at_rest=True,
                pii_redaction_required=True,
            ),
            DataCategory.CAREGIVER_REPORTS: RetentionPolicy(
                category=DataCategory.CAREGIVER_REPORTS,
                retention_period_seconds=90 * 86400.0,  # 90 days
                auto_purge_enabled=True,
                encrypt_at_rest=True,
                pii_redaction_required=False,
            ),
            DataCategory.LONG_TERM_MEMORY: RetentionPolicy(
                category=DataCategory.LONG_TERM_MEMORY,
                retention_period_seconds=365 * 86400.0,  # 365 days
                auto_purge_enabled=False,
                encrypt_at_rest=True,
                pii_redaction_required=False,
            ),
        }

        # Purge tracking
        self._total_purged_items = 0
        self._last_purge_timestamp = time.time()

    def get_policy(self, category: DataCategory) -> RetentionPolicy:
        with self._lock:
            return self._policies[category]

    def set_retention_period_days(self, category: DataCategory, days: float) -> None:
        with self._lock:
            self._policies[category].retention_period_seconds = max(1.0, days * 86400.0)

    def is_expired(self, category: DataCategory, created_timestamp: float) -> bool:
        policy = self.get_policy(category)
        if not policy.auto_purge_enabled:
            return False
        return (time.time() - created_timestamp) > policy.retention_period_seconds

    def purge_expired_records(
        self,
        audit_framework: Optional[Any] = None,
        working_memory: Optional[Any] = None,
        evidence_accumulator: Optional[Any] = None,
    ) -> Dict[str, int]:
        """
        Execute automated data retention purge across all managed subsystems.
        """
        purged_counts = {
            "working_memory_slots": 0,
            "evidence_records": 0,
            "audit_records": 0,
        }

        if working_memory:
            purged_counts["working_memory_slots"] = working_memory.expire_stale()

        if evidence_accumulator:
            # Purge evidence older than 24 hours
            purged_counts["evidence_records"] = evidence_accumulator.purge_decayed_evidence(max_age_seconds=86400.0)

        if audit_framework:
            audit_policy = self.get_policy(DataCategory.AUDIT_RECORDS)
            now = time.time()
            with audit_framework._lock:
                before = len(audit_framework._records)
                audit_framework._records = [
                    r for r in audit_framework._records
                    if (now - datetime.fromisoformat(r.timestamp_iso).timestamp()) <= audit_policy.retention_period_seconds
                ]
                purged_counts["audit_records"] = before - len(audit_framework._records)

        with self._lock:
            self._total_purged_items += sum(purged_counts.values())
            self._last_purge_timestamp = time.time()

        return purged_counts

    def secure_delete_patient_data(
        self,
        working_memory: Optional[Any] = None,
        audit_framework: Optional[Any] = None,
        evidence_accumulator: Optional[Any] = None,
    ) -> bool:
        """
        Execute emergency secure data deletion (GDPR / Consent Revocation compliance).
        Clears all in-memory transient & audit records.
        """
        if working_memory:
            working_memory.clear()
        if audit_framework:
            audit_framework.clear()
        if evidence_accumulator:
            evidence_accumulator.reset()

        print("[PrivacyManager] Secure data deletion executed. Transient and audit data wiped.")
        return True

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            policies_dict = {cat.value: pol.to_dict() for cat, pol in self._policies.items()}
            return {
                "total_purged_items": self._total_purged_items,
                "last_purge_timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self._last_purge_timestamp)),
                "policies": policies_dict,
            }
