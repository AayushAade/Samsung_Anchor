"""
MEMORA Versioned Runtime Configuration Profile Manager.

Provides operational runtime configuration profiles:
- DEVELOPMENT
- SIMULATION
- CLINICAL_DEMO
- PRODUCTION
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class RuntimeProfile(str, Enum):
    DEVELOPMENT = "DEVELOPMENT"
    SIMULATION = "SIMULATION"
    CLINICAL_DEMO = "CLINICAL_DEMO"
    PRODUCTION = "PRODUCTION"


@dataclass
class RuntimeConfig:
    profile: RuntimeProfile = RuntimeProfile.CLINICAL_DEMO
    max_memory_mb: int = 1024
    max_threads: int = 16
    log_level: str = "INFO"
    tracing_enabled: bool = True
    fault_isolation_enabled: bool = True
    audit_logging_enabled: bool = True
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile": self.profile.value,
            "max_memory_mb": self.max_memory_mb,
            "max_threads": self.max_threads,
            "log_level": self.log_level,
            "tracing_enabled": self.tracing_enabled,
            "fault_isolation_enabled": self.fault_isolation_enabled,
            "audit_logging_enabled": self.audit_logging_enabled,
            "version": self.version,
        }


class RuntimeConfigurationManager:
    """
    Thread-safe runtime configuration profile manager.
    """

    def __init__(self, profile: RuntimeProfile = RuntimeProfile.CLINICAL_DEMO) -> None:
        self._current_config = RuntimeConfig(profile=profile)
        self._lock = threading.Lock()

    def get_config(self) -> RuntimeConfig:
        with self._lock:
            return self._current_config

    def set_profile(self, profile: RuntimeProfile) -> RuntimeConfig:
        with self._lock:
            self._current_config.profile = profile
            if profile == RuntimeProfile.PRODUCTION:
                self._current_config.log_level = "WARNING"
                self._current_config.max_memory_mb = 2048
            elif profile == RuntimeProfile.DEVELOPMENT:
                self._current_config.log_level = "DEBUG"
            return self._current_config
