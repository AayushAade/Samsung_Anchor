"""
MEMORA Cognitive Integrity Explainer.

Generates deterministic Markdown summaries from IntegrityReport objects.
Produces pure string-formatted reports for clinical AI engineering auditability.
"""

from __future__ import annotations

from typing import List

from src.integrity.integrity_models import IntegrityIssue, IntegrityLevel, IntegrityReport


class IntegrityExplainer:
    """
    Deterministic Markdown narrative generator for ecosystem integrity reports.
    """

    @classmethod
    def explain_report(cls, report: IntegrityReport) -> str:
        lines = [
            "# MEMORA Cognitive Ecosystem Integrity Report",
            "",
            "## Executive Summary",
            f"- **Validation Time**: {report.validation_time}",
            f"- **Overall Health**: `{report.overall_status}`",
            f"- **Total Checks Conducted**: {report.total_checks}",
            f"- **Passed Checks**: {report.passed_checks}",
            f"- **Failed Checks / Issues**: {report.failed_checks}",
            f"- **Warning Count**: {report.warning_count}",
            "",
            "## Subsystem Breakdown",
        ]

        if not report.issues:
            lines.append("✅ All cognitive subsystems and cross-subsystem references are **100% HEALTHY** and consistent.")
            lines.append("")
            lines.append("## Recommended Actions")
            lines.append("• Maintain standard operational monitoring.")
            return "\n".join(lines)

        # Categorize issues by severity
        criticals: List[IntegrityIssue] = [i for i in report.issues if i.severity in (IntegrityLevel.CRITICAL, IntegrityLevel.ERROR)]
        warnings: List[IntegrityIssue] = [i for i in report.issues if i.severity in (IntegrityLevel.WARNING, IntegrityLevel.INFO)]

        if criticals:
            lines.append("### Critical Errors")
            for issue in criticals:
                lines.append(
                    f"- **[{issue.category.value}] {issue.subsystem}** (`{issue.severity.value}`): {issue.description}"
                )
                if issue.affected_reference:
                    lines.append(f"  - *Affected Reference*: `{issue.affected_reference}`")

        if warnings:
            lines.append("### Warnings & Diagnostics")
            for issue in warnings:
                lines.append(
                    f"- **[{issue.category.value}] {issue.subsystem}** (`{issue.severity.value}`): {issue.description}"
                )
                if issue.affected_reference:
                    lines.append(f"  - *Affected Reference*: `{issue.affected_reference}`")

        lines.append("")
        lines.append("## Recommended Actions")
        for issue in report.issues:
            if issue.recommendation:
                lines.append(f"• **{issue.subsystem}**: {issue.recommendation}")

        return "\n".join(lines)
