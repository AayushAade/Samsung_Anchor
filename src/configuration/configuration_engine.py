"""
MEMORA Central Configuration Engine.

Public façade providing unified, thread-safe entry points for configuration access,
policy retrieval, profile loading, snapshotting, freezing, and validation.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from src.configuration.configuration_models import (
    ConfigurationScope,
    ConfigurationSnapshot,
    ConfigurationSource,
    ConfigurationValue,
    PolicyDecision,
    PolicyRule,
    PolicyType,
)

from src.configuration.configuration_registry import ConfigurationRegistry
from src.configuration.policy_registry import PolicyRegistry
from src.configuration.configuration_validator import ConfigurationValidationReport, ConfigurationValidator


PROFILES: Dict[str, Dict[str, Any]] = {
    "DEVELOPMENT": {
        "system.target_fps": 30.0,
        "memory.max_active_records": 200,
        "runtime.max_memory_mb": 512,
    },
    "TESTING": {
        "system.target_fps": 60.0,
        "memory.max_active_records": 100,
        "runtime.max_memory_mb": 512,
    },
    "SIMULATION": {
        "system.target_fps": 60.0,
        "memory.max_active_records": 1000,
        "runtime.max_memory_mb": 1024,
    },
    "CLINICAL_DEMO": {
        "system.target_fps": 60.0,
        "memory.max_active_records": 500,
        "runtime.max_memory_mb": 1024,
    },
    "PRODUCTION": {
        "system.target_fps": 60.0,
        "memory.max_active_records": 2000,
        "runtime.max_memory_mb": 2048,
    },
}


class ConfigurationEngine:
    """
    Unified public façade for configuration and policy management.
    """

    def __init__(self, profile_name: str = "CLINICAL_DEMO") -> None:
        self.config_registry = ConfigurationRegistry()
        self.policy_registry = PolicyRegistry()
        self._current_profile = profile_name
        self._lock = threading.Lock()
        self.set_profile(profile_name)

    def get_configuration(self, key: str, default: Any = None) -> Any:
        return self.config_registry.get_value(key, default)

    def get_config_entry(self, key: str) -> Optional[ConfigurationValue]:
        return self.config_registry.get_config_entry(key)

    def get_policy(self, policy_type: PolicyType) -> List[PolicyRule]:
        return self.policy_registry.get_rules(policy_type)

    def evaluate_policy(self, policy_type: PolicyType, context: Dict[str, Any]) -> PolicyDecision:
        return self.policy_registry.evaluate_policy(policy_type, context)

    def set_profile(self, profile_name: str) -> None:
        with self._lock:
            prof = profile_name.upper()
            if prof not in PROFILES:
                raise ValueError(f"Unknown profile '{profile_name}'. Allowed profiles: {list(PROFILES.keys())}")

            self._current_profile = prof
            overrides = PROFILES[prof]
            for key, val in overrides.items():
                if self.config_registry.get_config_entry(key) is not None:
                    self.config_registry.set_value(key, val, source=ConfigurationSource.PROFILE_OVERRIDE)

    def get_current_profile(self) -> str:
        with self._lock:
            return self._current_profile

    def snapshot(self) -> ConfigurationSnapshot:
        with self._lock:
            chk = self.config_registry.compute_checksum()
            all_configs = self.config_registry.get_all()
            all_policies = self.policy_registry.get_all_rules()

            return ConfigurationSnapshot(
                profile_name=self._current_profile,
                is_frozen=self.config_registry.is_frozen(),
                values_count=len(all_configs),
                policies_count=len(all_policies),
                checksum=chk,
            )

    def validate(self) -> ConfigurationValidationReport:
        return ConfigurationValidator.validate(self.config_registry, self.policy_registry)

    def freeze(self) -> None:
        self.config_registry.freeze()

    def is_frozen(self) -> bool:
        return self.config_registry.is_frozen()

    def reset(self) -> None:
        with self._lock:
            self.config_registry.clear()
            self.policy_registry.clear()
            self.set_profile(self._current_profile)
