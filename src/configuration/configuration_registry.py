"""
MEMORA Central Configuration Registry.

Provides thread-safe registration, lookup, freezing, and snapshotting of all system configuration parameters.
Subsystems never own configuration; all read operations query this registry.
"""

from __future__ import annotations

import hashlib
import json
import threading
from typing import Any, Dict, List, Optional

from src.configuration.configuration_models import (
    ConfigurationScope,
    ConfigurationSource,
    ConfigurationValue,
)


class ConfigurationRegistry:
    """
    Thread-safe, freezable configuration registry.
    """

    def __init__(self) -> None:
        self._entries: Dict[str, ConfigurationValue] = {}
        self._is_frozen: bool = False
        self._lock = threading.Lock()
        self._seed_default_configurations()

    def register_config(self, entry: ConfigurationValue) -> None:
        with self._lock:
            if self._is_frozen:
                raise RuntimeError("Configuration registry is frozen; cannot register new parameters.")
            self._entries[entry.key] = entry

    def get_value(self, key: str, default: Any = None) -> Any:
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None:
                return entry.value
            return default

    def get_config_entry(self, key: str) -> Optional[ConfigurationValue]:
        with self._lock:
            return self._entries.get(key)

    def set_value(
        self,
        key: str,
        value: Any,
        source: ConfigurationSource = ConfigurationSource.EXPLICIT_SET,
    ) -> None:
        with self._lock:
            if self._is_frozen:
                raise RuntimeError("Configuration registry is frozen; modification is prohibited.")
            if key not in self._entries:
                raise KeyError(f"Configuration key '{key}' is not registered.")
            entry = self._entries[key]
            entry.value = value
            entry.source = source

    def get_all(self) -> Dict[str, ConfigurationValue]:
        with self._lock:
            return dict(self._entries)

    def freeze(self) -> None:
        with self._lock:
            self._is_frozen = True

    def is_frozen(self) -> bool:
        with self._lock:
            return self._is_frozen

    def compute_checksum(self) -> str:
        with self._lock:
            data = {k: v.value for k, v in sorted(self._entries.items())}
            raw = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
            return hashlib.sha256(raw).hexdigest()[:16]

    def export_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {k: v.value for k, v in self._entries.items()}

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self._is_frozen = False
            self._seed_default_configurations()

    def _seed_default_configurations(self) -> None:
        """Seed baseline defaults across all 8 configuration scopes."""
        defaults = [
            ConfigurationValue("system.name", "MEMORA", "MEMORA", ConfigurationScope.SYSTEM, description="Platform identifier"),
            ConfigurationValue("system.target_fps", 60.0, 60.0, ConfigurationScope.SYSTEM, min_value=1.0, max_value=120.0, description="Target pipeline frame rate"),
            ConfigurationValue("memory.max_active_records", 500, 500, ConfigurationScope.MEMORY, min_value=10, max_value=5000, description="Maximum active long-term memories"),
            ConfigurationValue("memory.retention_days", 30, 30, ConfigurationScope.MEMORY, min_value=1, max_value=365, description="Default temporary retention age"),
            ConfigurationValue("reasoning.confidence_threshold", 0.70, 0.70, ConfigurationScope.REASONING, min_value=0.0, max_value=1.0, description="Minimum confidence threshold for reasoning hypotheses"),
            ConfigurationValue("executive.max_goal_depth", 5, 5, ConfigurationScope.EXECUTIVE, min_value=1, max_value=20, description="Maximum depth for hierarchical task DAGs"),
            ConfigurationValue("trust.pii_redaction_enabled", True, True, ConfigurationScope.TRUST, description="Enforce automatic PII redaction"),
            ConfigurationValue("runtime.max_memory_mb", 1024, 1024, ConfigurationScope.RUNTIME, min_value=256, max_value=8192, description="Maximum process RSS limit"),
            ConfigurationValue("session.max_trace_steps", 100, 100, ConfigurationScope.SESSION, min_value=10, max_value=1000, description="Maximum execution steps recorded per session"),
        ]
        for entry in defaults:
            self._entries[entry.key] = entry
