"""
MEMORA Audit & Traceability Framework — Audit Framework.

Generates structured, privacy-conscious audit records for every meaningful cognitive action.
Supports PII redaction/hashing and structured JSON/CSV export formats.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.trust.models import AuditExportFormat, TrustAuditRecord


class AuditFramework:
    """
    Observer audit logger producing privacy-conscious TrustAuditRecords.
    """

    MAX_RECORDS = 500

    def __init__(self, max_records: int = 500, redact_pii_by_default: bool = True) -> None:
        self.max_records = max_records
        self.redact_pii_by_default = redact_pii_by_default
        self._records: List[TrustAuditRecord] = []
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_audit(
        self,
        cycle_id: int,
        triggering_event: str,
        active_goal: Optional[str],
        active_context_summary: str,
        working_memory_keys: List[str],
        selected_care_policy: str,
        evidence_summary: str,
        safety_status: str,
        safety_checks_passed: int,
        safety_checks_failed: List[str],
        proposed_action: str,
        final_action: str,
        explanation: str,
        patient_name: Optional[str] = None,
    ) -> TrustAuditRecord:
        """
        Record a structured audit entry.
        """
        audit_id = f"aud-{uuid.uuid4().hex[:8]}"

        # Redact PII if configured
        ctx_summary = active_context_summary
        expl = explanation
        if self.redact_pii_by_default and patient_name:
            hashed_name = f"Subject#{hashlib.sha256(patient_name.encode()).hexdigest()[:6]}"
            ctx_summary = ctx_summary.replace(patient_name, hashed_name)
            expl = expl.replace(patient_name, hashed_name)

        record = TrustAuditRecord(
            audit_id=audit_id,
            timestamp_iso=datetime.now().isoformat(),
            cycle_id=cycle_id,
            triggering_event=triggering_event,
            active_goal=active_goal,
            active_context_summary=ctx_summary,
            working_memory_keys=working_memory_keys,
            selected_care_policy=selected_care_policy,
            evidence_summary=evidence_summary,
            safety_status=safety_status,
            safety_checks_passed=safety_checks_passed,
            safety_checks_failed=safety_checks_failed,
            proposed_action=proposed_action,
            final_action=final_action,
            explanation=expl,
            pii_redacted=self.redact_pii_by_default,
        )

        with self._lock:
            self._records.append(record)
            if len(self._records) > self.max_records:
                self._records = self._records[-self.max_records:]

        return record

    def export_records(self, fmt: AuditExportFormat = AuditExportFormat.JSON) -> str:
        """
        Export captured audit records in the requested format (JSON, CSV, REDACTED_JSON).
        """
        with self._lock:
            snapshot = [r.to_dict() for r in self._records]

        if fmt == AuditExportFormat.JSON:
            return json.dumps(snapshot, indent=2)

        if fmt == AuditExportFormat.REDACTED_JSON:
            # Enforce redaction on exported json
            for item in snapshot:
                item["pii_redacted"] = True
            return json.dumps(snapshot, indent=2)

        if fmt == AuditExportFormat.CSV:
            if not snapshot:
                return "audit_id,timestamp,cycle_id,triggering_event,safety_status,final_action\n"
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=list(snapshot[0].keys()))
            writer.writeheader()
            for r in snapshot:
                row = dict(r)
                row["working_memory_keys"] = ";".join(row.get("working_memory_keys", []))
                row["safety_checks_failed"] = ";".join(row.get("safety_checks_failed", []))
                writer.writerow(row)
            return output.getvalue()

        return json.dumps(snapshot)

    def get_recent_records(self, limit: int = 10) -> List[TrustAuditRecord]:
        with self._lock:
            return list(self._records[-limit:])

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
