"""
MEMORA Unified Configuration & Policy Framework Data Models.

Defines immutable value objects, enums, rules, decisions, and snapshots for system configuration and policy enforcement.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ConfigurationScope(str, Enum):
    SYSTEM = "SYSTEM"
    COGNITIVE = "COGNITIVE"
    TRUST = "TRUST"
    MEMORY = "MEMORY"
    REASONING = "REASONING"
    EXECUTIVE = "EXECUTIVE"
    RUNTIME = "RUNTIME"
    SESSION = "SESSION"


class ConfigurationSource(str, Enum):
    DEFAULT = "DEFAULT"
    PROFILE_OVERRIDE = "PROFILE_OVERRIDE"
    EXPLICIT_SET = "EXPLICIT_SET"


class PolicyType(str, Enum):
    MEMORY_RETENTION = "MEMORY_RETENTION"
    EXECUTIVE_PLANNING = "EXECUTIVE_PLANNING"
    SAFETY_GUARDRAILS = "SAFETY_GUARDRAILS"
    RUNTIME_RESOURCES = "RUNTIME_RESOURCES"
    REASONING_CONFIDENCE = "REASONING_CONFIDENCE"
    TRUST_PRIVACY = "TRUST_PRIVACY"
    SESSION_LIFECYCLE = "SESSION_LIFECYCLE"


@dataclass
class ConfigurationValue:
    """
    Represents a single typed configuration parameter with validation bounds.
    """

    key: str
    value: Any
    default_value: Any
    scope: ConfigurationScope
    source: ConfigurationSource = ConfigurationSource.DEFAULT
    description: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "default_value": self.default_value,
            "scope": self.scope.value,
            "source": self.source.value,
            "description": self.description,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "allowed_values": self.allowed_values,
        }


@dataclass
class PolicyRule:
    """
    Represents a single structured policy rule.
    """

    rule_id: str
    policy_type: PolicyType
    name: str
    rule_condition: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "policy_type": self.policy_type.value,
            "name": self.name,
            "rule_condition": self.rule_condition,
            "parameters": dict(self.parameters),
            "description": self.description,
        }


@dataclass
class PolicyDecision:
    """
    Represents the result of evaluating a policy against given execution parameters.
    """

    policy_type: PolicyType
    is_allowed: bool
    rationale: str
    applied_rules: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_type": self.policy_type.value,
            "is_allowed": self.is_allowed,
            "rationale": self.rationale,
            "applied_rules": list(self.applied_rules),
        }


@dataclass
class ConfigurationSnapshot:
    """
    Point-in-time immutable snapshot of configuration and policy registries.
    """

    profile_name: str
    is_frozen: bool
    values_count: int
    policies_count: int
    checksum: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "profile_name": self.profile_name,
            "is_frozen": self.is_frozen,
            "values_count": self.values_count,
            "policies_count": self.policies_count,
            "checksum": self.checksum,
        }
