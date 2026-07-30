"""
MEMORA Central Policy Registry.

Stores deterministic, structured PolicyRule objects grouped by PolicyType.
Provides policy lookup and evaluation without executable business logic or external dependencies.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from src.configuration.configuration_models import PolicyDecision, PolicyRule, PolicyType


class PolicyRegistry:
    """
    Thread-safe registry for system-wide policy rules.
    """

    def __init__(self) -> None:
        self._rules: Dict[str, PolicyRule] = {}
        self._lock = threading.Lock()
        self._seed_default_policies()

    def register_policy_rule(self, rule: PolicyRule) -> None:
        with self._lock:
            self._rules[rule.rule_id] = rule

    def get_rules(self, policy_type: PolicyType) -> List[PolicyRule]:
        with self._lock:
            return [r for r in self._rules.values() if r.policy_type == policy_type]

    def get_all_rules(self) -> List[PolicyRule]:
        with self._lock:
            return list(self._rules.values())

    def evaluate_policy(self, policy_type: PolicyType, context: Dict[str, Any]) -> PolicyDecision:
        """
        Evaluate context parameters against registered policy rules for a given PolicyType.
        Returns a deterministic PolicyDecision.
        """
        rules = self.get_rules(policy_type)
        applied_rules: List[str] = []
        is_allowed = True
        reasons: List[str] = []

        for rule in rules:
            applied_rules.append(rule.rule_id)
            # Evaluate rule parameter bounds against context
            for param_key, param_limit in rule.parameters.items():
                if param_key in context:
                    actual_val = context[param_key]
                    if isinstance(param_limit, (int, float)) and isinstance(actual_val, (int, float)):
                        if "max" in rule.rule_condition.lower() and actual_val > param_limit:
                            is_allowed = False
                            reasons.append(f"Rule `{rule.rule_id}` violated: {param_key} ({actual_val}) exceeds max ({param_limit}).")
                        elif "min" in rule.rule_condition.lower() and actual_val < param_limit:
                            is_allowed = False
                            reasons.append(f"Rule `{rule.rule_id}` violated: {param_key} ({actual_val}) below min ({param_limit}).")

        rationale = "; ".join(reasons) if reasons else f"Policy `{policy_type.value}` satisfied by {len(applied_rules)} rules."
        return PolicyDecision(
            policy_type=policy_type,
            is_allowed=is_allowed,
            rationale=rationale,
            applied_rules=applied_rules,
        )

    def clear(self) -> None:
        with self._lock:
            self._rules.clear()
            self._seed_default_policies()

    def _seed_default_policies(self) -> None:
        """Seed baseline policy rules."""
        defaults = [
            PolicyRule("pol-mem-01", PolicyType.MEMORY_RETENTION, "Clinical Expiration Protection", "NEVER_EXPIRE_CLINICAL", {"never_expire": True}, "Clinical records must never expire"),
            PolicyRule("pol-exec-01", PolicyType.EXECUTIVE_PLANNING, "Max Plan Depth Limit", "MAX_DEPTH_CHECK", {"depth": 5}, "Executive goals must not exceed max depth"),
            PolicyRule("pol-safe-01", PolicyType.SAFETY_GUARDRAILS, "Strict Caregiver Override", "CAREGIVER_OVERRIDE", {"override_priority": 1}, "Caregiver overrides supersede all actions"),
            PolicyRule("pol-rt-01", PolicyType.RUNTIME_RESOURCES, "Memory RSS Ceiling", "MAX_RSS_CHECK", {"memory_mb": 2048}, "Process memory RSS limit"),
            PolicyRule("pol-reas-01", PolicyType.REASONING_CONFIDENCE, "Reasoning Confidence Floor", "MIN_CONFIDENCE_CHECK", {"confidence": 0.50}, "Minimum confidence required for reasoning action"),
            PolicyRule("pol-trust-01", PolicyType.TRUST_PRIVACY, "PII Masking Requirement", "ALWAYS_MASK_PII", {"mask_pii": True}, "Enforce strict PII masking"),
            PolicyRule("pol-ses-01", PolicyType.SESSION_LIFECYCLE, "Session Timeout Guard", "MAX_DURATION_CHECK", {"duration_sec": 300}, "Maximum single session execution duration"),
        ]
        for rule in defaults:
            self._rules[rule.rule_id] = rule
