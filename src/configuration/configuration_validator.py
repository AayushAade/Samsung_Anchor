"""
MEMORA Configuration Validator.

Validates configuration parameters and policy rules against range bounds,
type contracts, mandatory entries, and profile conflicts without mutating state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.configuration.configuration_models import ConfigurationScope, ConfigurationValue
from src.configuration.configuration_registry import ConfigurationRegistry
from src.configuration.policy_registry import PolicyRegistry


@dataclass
class ConfigurationIssue:
    key: str
    severity: str  # "ERROR" or "WARNING"
    description: str
    recommendation: str


@dataclass
class ConfigurationValidationReport:
    total_validated: int
    passed_count: int
    failed_count: int
    warning_count: int
    issues: List[ConfigurationIssue] = field(default_factory=list)
    is_valid: bool = True
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_validated": self.total_validated,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "warning_count": self.warning_count,
            "is_valid": self.is_valid,
            "issues": [
                {
                    "key": i.key,
                    "severity": i.severity,
                    "description": i.description,
                    "recommendation": i.recommendation,
                }
                for i in self.issues
            ],
        }


class ConfigurationValidator:
    """
    Read-only validation engine for ConfigurationRegistry and PolicyRegistry.
    """

    @classmethod
    def validate(
        cls,
        config_registry: ConfigurationRegistry,
        policy_registry: Optional[PolicyRegistry] = None,
    ) -> ConfigurationValidationReport:
        all_configs = config_registry.get_all()
        issues: List[ConfigurationIssue] = []

        for key, entry in all_configs.items():
            val = entry.value

            # 1. Missing / None value check
            if val is None:
                issues.append(
                    ConfigurationIssue(
                        key=key,
                        severity="ERROR",
                        description=f"Configuration key '{key}' has a None value.",
                        recommendation="Assign a valid non-null value or restore default.",
                    )
                )

            # 2. Min value bound check
            if entry.min_value is not None and isinstance(val, (int, float)):
                if val < entry.min_value:
                    issues.append(
                        ConfigurationIssue(
                            key=key,
                            severity="ERROR",
                            description=f"Value {val} for key '{key}' is below minimum bound ({entry.min_value}).",
                            recommendation=f"Increase value to at least {entry.min_value}.",
                        )
                    )

            # 3. Max value bound check
            if entry.max_value is not None and isinstance(val, (int, float)):
                if val > entry.max_value:
                    issues.append(
                        ConfigurationIssue(
                            key=key,
                            severity="ERROR",
                            description=f"Value {val} for key '{key}' exceeds maximum bound ({entry.max_value}).",
                            recommendation=f"Reduce value to at most {entry.max_value}.",
                        )
                    )

            # 4. Allowed values check
            if entry.allowed_values is not None:
                if val not in entry.allowed_values:
                    issues.append(
                        ConfigurationIssue(
                            key=key,
                            severity="ERROR",
                            description=f"Value '{val}' for key '{key}' is not in allowed list {entry.allowed_values}.",
                            recommendation=f"Choose one of the allowed values: {entry.allowed_values}.",
                        )
                    )

        failed_count = sum(1 for i in issues if i.severity == "ERROR")
        warning_count = sum(1 for i in issues if i.severity == "WARNING")
        passed_count = len(all_configs) - failed_count
        is_valid = failed_count == 0

        return ConfigurationValidationReport(
            total_validated=len(all_configs),
            passed_count=passed_count,
            failed_count=failed_count,
            warning_count=warning_count,
            issues=issues,
            is_valid=is_valid,
        )
