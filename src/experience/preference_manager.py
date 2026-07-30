"""
MEMORA Caregiver Preference Manager.

Manages explicit, editable caregiver operational preferences:
- Preferred reminder timing
- Communication verbosity & style
- Escalation thresholds
- Recovery strategies
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from src.experience.experience_models import CaregiverPreference


class CaregiverPreferenceManager:
    """
    Thread-safe manager for caregiver operational preferences.
    """

    def __init__(self) -> None:
        self._preferences: Dict[str, CaregiverPreference] = {}
        self._lock = threading.Lock()
        self._seed_baseline_preferences()

    def set_preference(
        self, key: str, value: Any, category: str = "GENERAL", description: str = ""
    ) -> CaregiverPreference:
        pref = CaregiverPreference(
            preference_key=key,
            preference_value=value,
            category=category,
            description=description,
        )
        with self._lock:
            self._preferences[key] = pref
        return pref

    def get_preference(self, key: str, default: Any = None) -> Any:
        with self._lock:
            pref = self._preferences.get(key)
            return pref.preference_value if pref else default

    def get_all_preferences(self) -> List[CaregiverPreference]:
        with self._lock:
            return list(self._preferences.values())

    def _seed_baseline_preferences(self) -> None:
        """Seed baseline caregiver preferences."""
        p1 = CaregiverPreference(
            preference_key="preferred_reminder_timing",
            preference_value="08:30 AM",
            category="ROUTINE",
            description="Morning medication cue target time",
        )
        p2 = CaregiverPreference(
            preference_key="preferred_communication_style",
            preference_value="GENTLE_ORIENTATION",
            category="COMMUNICATION",
            description="Care policy communication principle",
        )
        p3 = CaregiverPreference(
            preference_key="preferred_recovery_strategy",
            preference_value="FALLBACK",
            category="EXECUTIVE",
            description="Default task failure recovery strategy",
        )
        self._preferences[p1.preference_key] = p1
        self._preferences[p2.preference_key] = p2
        self._preferences[p3.preference_key] = p3
