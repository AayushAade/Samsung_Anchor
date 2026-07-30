"""
MEMORA Configuration Explainer.

Generates deterministic Markdown summaries of configuration states, active deployment profiles,
policy rules, and validation reports for clinical engineering diagnostics.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.configuration.configuration_engine import ConfigurationEngine
from src.configuration.configuration_validator import ConfigurationValidationReport


class ConfigurationExplainer:
    """
    Deterministic Markdown narrative generator for configuration and policy diagnostics.
    """

    @classmethod
    def explain_engine_state(
        cls,
        engine: ConfigurationEngine,
        report: Optional[ConfigurationValidationReport] = None,
    ) -> str:
        snapshot = engine.snapshot()
        val_report = report or engine.validate()
        configs = engine.config_registry.get_all()
        policies = engine.policy_registry.get_all_rules()

        lines = [
            "# MEMORA Unified Configuration & Policy Diagnostic Report",
            "",
            "## Executive Summary",
            f"- **Deployment Profile**: `{snapshot.profile_name}`",
            f"- **Registry Status**: `{'FROZEN (Read-Only)' if snapshot.is_frozen else 'ACTIVE'}`",
            f"- **Configuration Parameters**: {snapshot.values_count}",
            f"- **Registered Policy Rules**: {snapshot.policies_count}",
            f"- **Checksum (SHA256)**: `{snapshot.checksum}`",
            f"- **Validation Status**: `{'PASSED (Valid)' if val_report.is_valid else 'FAILED (Issues Detected)'}`",
            "",
            "## Configuration Parameters Summary",
        ]

        for key, entry in sorted(configs.items()):
            lines.append(
                f"- **`{key}`**: `{entry.value}` (Default: `{entry.default_value}`, Scope: `{entry.scope.value}`, Source: `{entry.source.value}`)"
            )

        lines.append("")
        lines.append("## Registered Policy Summary")
        for pol in sorted(policies, key=lambda p: p.rule_id):
            lines.append(
                f"- **`{pol.rule_id}`** [{pol.policy_type.value}]: *{pol.name}* — {pol.description}"
            )

        lines.append("")
        lines.append("## Validation Results & Diagnostics")
        lines.append(f"- **Total Validated**: {val_report.total_validated}")
        lines.append(f"- **Passed**: {val_report.passed_count}")
        lines.append(f"- **Failed / Errors**: {val_report.failed_count}")
        lines.append(f"- **Warnings**: {val_report.warning_count}")

        if val_report.issues:
            lines.append("")
            lines.append("### Detected Issues")
            for issue in val_report.issues:
                lines.append(f"- **[{issue.severity}] `{issue.key}`**: {issue.description}")
                lines.append(f"  - *Recommendation*: {issue.recommendation}")
        else:
            lines.append("✅ All configuration parameters and policy bounds are **100% VALID**.")

        lines.append("")
        lines.append("## Recommended Actions")
        if not snapshot.is_frozen:
            lines.append("• Freeze the configuration registry prior to production pipeline deployment.")
        lines.append("• Maintain profile inheritance alignment across deployment environments.")

        return "\n".join(lines)
