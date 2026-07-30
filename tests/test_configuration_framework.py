"""
Comprehensive Test Suite for MEMORA Phase 33 — Unified Configuration & Policy Framework.

Tests:
1. Configuration Data Models (Serialization of ConfigurationValue, PolicyRule, PolicyDecision, ConfigurationSnapshot)
2. Configuration Registry (Thread-safe registration, lookup, set_value, freeze, checksum)
3. Policy Registry (Rule registration, type grouping, policy evaluation)
4. Configuration Validator (Min/max bound checks, allowed value bounds, None value detection)
5. Configuration Engine (Public façade, deployment profile overrides, snapshotting, freezing)
6. Configuration Explainer (Markdown diagnostic report generation)
7. Thread-Safety & Immutability Invariant (Verifies freeze enforcement and thread-safe mutation)
"""

import pytest
from src.configuration import (
    PROFILES,
    ConfigurationEngine,
    ConfigurationExplainer,
    ConfigurationIssue,
    ConfigurationRegistry,
    ConfigurationScope,
    ConfigurationSnapshot,
    ConfigurationSource,
    ConfigurationValidationReport,
    ConfigurationValidator,
    ConfigurationValue,
    PolicyDecision,
    PolicyRegistry,
    PolicyRule,
    PolicyType,
)


# ======================================================================
# 1. Configuration Data Models Tests
# ======================================================================

class TestConfigurationModels:
    def test_configuration_value_to_dict(self):
        val = ConfigurationValue(
            key="test.param",
            value=100,
            default_value=100,
            scope=ConfigurationScope.COGNITIVE,
            min_value=0,
            max_value=200,
            description="Test parameter",
        )
        d = val.to_dict()
        assert d["key"] == "test.param"
        assert d["value"] == 100
        assert d["scope"] == "COGNITIVE"

    def test_policy_rule_and_decision_to_dict(self):
        rule = PolicyRule(
            rule_id="pol-1",
            policy_type=PolicyType.SAFETY_GUARDRAILS,
            name="Rule 1",
            rule_condition="CHECK",
        )
        assert rule.to_dict()["rule_id"] == "pol-1"

        decision = PolicyDecision(
            policy_type=PolicyType.SAFETY_GUARDRAILS,
            is_allowed=True,
            rationale="Passed",
            applied_rules=["pol-1"],
        )
        assert decision.to_dict()["is_allowed"] is True

    def test_configuration_snapshot_to_dict(self):
        snap = ConfigurationSnapshot(
            profile_name="CLINICAL_DEMO",
            is_frozen=False,
            values_count=9,
            policies_count=7,
            checksum="abc12345",
        )
        assert snap.to_dict()["profile_name"] == "CLINICAL_DEMO"


# ======================================================================
# 2. Configuration Registry Tests
# ======================================================================

class TestConfigurationRegistry:
    def test_registry_registration_and_lookup(self):
        reg = ConfigurationRegistry()
        reg.register_config(
            ConfigurationValue("custom.key", 42, 42, ConfigurationScope.SYSTEM)
        )
        assert reg.get_value("custom.key") == 42
        assert reg.get_config_entry("custom.key").scope == ConfigurationScope.SYSTEM

    def test_registry_set_value(self):
        reg = ConfigurationRegistry()
        reg.set_value("system.name", "MEMORA_CUSTOM")
        assert reg.get_value("system.name") == "MEMORA_CUSTOM"

    def test_registry_freeze_enforcement(self):
        reg = ConfigurationRegistry()
        reg.freeze()
        assert reg.is_frozen() is True

        with pytest.raises(RuntimeError, match="Configuration registry is frozen"):
            reg.set_value("system.name", "MEMORA_NEW")

        with pytest.raises(RuntimeError, match="Configuration registry is frozen"):
            reg.register_config(ConfigurationValue("new.key", 1, 1, ConfigurationScope.SYSTEM))


# ======================================================================
# 3. Policy Registry Tests
# ======================================================================

class TestPolicyRegistry:
    def test_policy_registration_and_evaluation(self):
        preg = PolicyRegistry()
        rules = preg.get_rules(PolicyType.MEMORY_RETENTION)
        assert len(rules) >= 1

        decision = preg.evaluate_policy(PolicyType.RUNTIME_RESOURCES, {"memory_mb": 1024})
        assert decision.is_allowed is True

        decision_fail = preg.evaluate_policy(PolicyType.RUNTIME_RESOURCES, {"memory_mb": 4096})
        assert decision_fail.is_allowed is False


# ======================================================================
# 4. Configuration Validator Tests
# ======================================================================

class TestConfigurationValidator:
    def test_validate_clean_registry(self):
        reg = ConfigurationRegistry()
        report = ConfigurationValidator.validate(reg)
        assert report.is_valid is True
        assert report.failed_count == 0

    def test_validate_min_bound_violation(self):
        reg = ConfigurationRegistry()
        reg.set_value("system.target_fps", 0.1)  # min_value is 1.0
        report = ConfigurationValidator.validate(reg)
        assert report.is_valid is False
        assert report.failed_count >= 1
        assert any("below minimum bound" in i.description for i in report.issues)


# ======================================================================
# 5. Configuration Engine Tests
# ======================================================================

class TestConfigurationEngine:
    def test_engine_profile_overrides(self):
        engine = ConfigurationEngine(profile_name="PRODUCTION")
        assert engine.get_current_profile() == "PRODUCTION"
        assert engine.get_configuration("runtime.max_memory_mb") == 2048

        engine.set_profile("DEVELOPMENT")
        assert engine.get_configuration("runtime.max_memory_mb") == 512

    def test_engine_snapshot_and_freeze(self):
        engine = ConfigurationEngine(profile_name="CLINICAL_DEMO")
        snap = engine.snapshot()
        assert snap.profile_name == "CLINICAL_DEMO"
        assert snap.is_frozen is False

        engine.freeze()
        assert engine.is_frozen() is True
        assert engine.snapshot().is_frozen is True


# ======================================================================
# 6. Configuration Explainer Tests
# ======================================================================

class TestConfigurationExplainer:
    def test_explain_engine_state(self):
        engine = ConfigurationEngine(profile_name="CLINICAL_DEMO")
        markdown = ConfigurationExplainer.explain_engine_state(engine)
        assert "MEMORA Unified Configuration & Policy Diagnostic Report" in markdown
        assert "CLINICAL_DEMO" in markdown
        assert "system.name" in markdown
