"""
MEMORA Security Explainer.

Generates deterministic Markdown summaries of registered identities, role permissions,
security audit logs, and access decisions for clinical engineering diagnostics.
"""

from __future__ import annotations

from typing import List

from src.security.security_engine import SecurityEngine


class SecurityExplainer:
    """
    Deterministic Markdown narrative generator for security and identity access reports.
    """

    @classmethod
    def explain_security_state(cls, engine: SecurityEngine) -> str:
        snap = engine.snapshot()
        identities = engine.list_identities()
        audits = engine.audit_log()
        denied_audits = [a for a in audits if not a.granted]

        lines = [
            "# MEMORA Security, Identity & Access Control Diagnostic Report",
            "",
            "## Executive Summary",
            f"- **Registered Identities Count**: {snap.identities_count}",
            f"- **Active Enabled Identities**: {snap.active_identities_count}",
            f"- **Unique Roles Represented**: {snap.roles_count}",
            f"- **Registry Checksum (SHA256)**: `{snap.checksum}`",
            f"- **Total Security Audit Log Events**: {len(audits)}",
            f"- **Denied Access Requests Count**: {len(denied_audits)}",
            "",
            "## Registered Identity Summary",
        ]

        for ident in sorted(identities, key=lambda i: i.identity_id):
            status_str = "ENABLED" if ident.enabled else "DISABLED"
            lines.append(
                f"- **`{ident.identity_id}`** ({ident.display_name}) — Role: `{ident.role.value}` [{status_str}]"
            )

        lines.append("")
        lines.append("## Permission Matrix & Granted Rights")
        for ident in sorted(identities, key=lambda i: i.identity_id):
            perms_str = ", ".join([p.value for p in ident.permissions]) if ident.permissions else "Default Role Matrix"
            lines.append(f"- `{ident.identity_id}` ({ident.role.value}): {perms_str}")

        lines.append("")
        lines.append("## Authorization & Audit Overview")
        lines.append(f"- **Total Evaluated Requests**: {len(audits)}")
        lines.append(f"- **Granted Requests**: {len(audits) - len(denied_audits)}")
        lines.append(f"- **Denied Requests**: {len(denied_audits)}")

        if denied_audits:
            lines.append("")
            lines.append("### Denied Access Request Details")
            for entry in denied_audits:
                lines.append(
                    f"- **[{entry.timestamp}] `{entry.identity_id}`** requested `{entry.requested_operation}` → Denied: {entry.denial_reason}"
                )
        else:
            lines.append("✅ Zero unauthorized or denied access attempts recorded.")

        lines.append("")
        lines.append("## Recommended Actions")
        if any(not i.enabled for i in identities):
            lines.append("• Review disabled identities to ensure proper access revocation.")
        lines.append("• Audit role permission assignments regularly prior to production deployment.")

        return "\n".join(lines)
