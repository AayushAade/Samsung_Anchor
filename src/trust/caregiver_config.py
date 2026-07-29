"""
MEMORA Caregiver Configuration Framework — Caregiver Config Manager.

Allows caregivers or operators to configure key behavioural preferences
without modifying source code. Provides schema validation and safe defaults.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class CaregiverPreferences:
    """Configurable behavioural preferences for MEMORA."""
    reminder_frequency_minutes: float = 30.0
    min_confidence_threshold: float = 0.35
    preferred_care_strategy: str = "Validation Therapy"
    quiet_hours_start: int = 22  # 10 PM
    quiet_hours_end: int = 7     # 7 AM
    escalation_behaviour: str = "IMMEDIATE"  # IMMEDIATE, CAREGIVER_SMS, AUDIBLE_ALERT
    speech_verbosity: str = "CONCISE"         # CONCISE, DETAILED, MINIMAL
    object_persistence_hours: float = 24.0
    enable_tactile_haptics: bool = False
    allow_ambient_monitoring: bool = True

    def validate(self) -> List[str]:
        """Validate configuration values and return a list of error messages."""
        errors: List[str] = []
        if not (1.0 <= self.reminder_frequency_minutes <= 1440.0):
            errors.append(f"reminder_frequency_minutes ({self.reminder_frequency_minutes}) must be between 1 and 1440.")
        if not (0.05 <= self.min_confidence_threshold <= 0.95):
            errors.append(f"min_confidence_threshold ({self.min_confidence_threshold}) must be between 0.05 and 0.95.")
        if not (0 <= self.quiet_hours_start <= 23):
            errors.append(f"quiet_hours_start ({self.quiet_hours_start}) must be between 0 and 23.")
        if not (0 <= self.quiet_hours_end <= 23):
            errors.append(f"quiet_hours_end ({self.quiet_hours_end}) must be between 0 and 23.")
        if self.escalation_behaviour not in ("IMMEDIATE", "CAREGIVER_SMS", "AUDIBLE_ALERT"):
            errors.append(f"Invalid escalation_behaviour '{self.escalation_behaviour}'.")
        if self.speech_verbosity not in ("CONCISE", "DETAILED", "MINIMAL"):
            errors.append(f"Invalid speech_verbosity '{self.speech_verbosity}'.")
        if not (0.5 <= self.object_persistence_hours <= 168.0):
            errors.append(f"object_persistence_hours ({self.object_persistence_hours}) must be between 0.5 and 168.0.")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CaregiverConfigManager:
    """
    Manager loading and validating caregiver preferences from JSON file or dictionary.
    Falls back gracefully to safe defaults if file is missing or invalid.
    """

    DEFAULT_CONFIG_PATH = "caregiver_config.json"

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._preferences = CaregiverPreferences()
        self._lock = threading.Lock()
        self._last_loaded_errors: List[str] = []

        # Load configuration on init
        self.reload()

    def reload(self) -> bool:
        """Reload configuration from disk. Returns True if successfully loaded."""
        with self._lock:
            if not os.path.exists(self.config_path):
                self._preferences = CaregiverPreferences()
                self._last_loaded_errors = []
                return False

            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                prefs = CaregiverPreferences(**data)
                errors = prefs.validate()

                if errors:
                    self._last_loaded_errors = errors
                    print(f"[CaregiverConfigManager] Validation errors in {self.config_path}: {errors}. Using defaults.")
                    self._preferences = CaregiverPreferences()
                    return False

                self._preferences = prefs
                self._last_loaded_errors = []
                return True

            except Exception as e:
                self._last_loaded_errors = [f"Failed to parse config file: {e}"]
                print(f"[CaregiverConfigManager] Error reading {self.config_path}: {e}. Using defaults.")
                self._preferences = CaregiverPreferences()
                return False

    def update(self, updates: Dict[str, Any]) -> List[str]:
        """Update caregiver preferences in-memory with validation."""
        with self._lock:
            current_dict = self._preferences.to_dict()
            current_dict.update(updates)
            try:
                new_prefs = CaregiverPreferences(**current_dict)
                errors = new_prefs.validate()
                if errors:
                    return errors
                self._preferences = new_prefs
                return []
            except Exception as e:
                return [f"Invalid preference keys or types: {e}"]

    def save(self, filepath: Optional[str] = None) -> bool:
        """Save current preferences to JSON file."""
        target_path = filepath or self.config_path
        with self._lock:
            try:
                with open(target_path, "w", encoding="utf-8") as f:
                    json.dump(self._preferences.to_dict(), f, indent=2)
                return True
            except Exception as e:
                print(f"[CaregiverConfigManager] Error saving to {target_path}: {e}")
                return False

    def get_preferences(self) -> CaregiverPreferences:
        with self._lock:
            return self._preferences

    def get_validation_errors(self) -> List[str]:
        with self._lock:
            return list(self._last_loaded_errors)
