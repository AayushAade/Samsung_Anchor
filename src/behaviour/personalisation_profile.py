"""
MEMORA Personalised Assistance Profile.

Manages explainable, reviewable, and caregiver-overrideable personalization preferences:
- Preferred reminder styles
- Speech verbosity
- Frequently contacted family members
- Preferred object resting locations
- Effective care strategies
- Typical daily schedule anchors
"""

from __future__ import annotations

import json
import threading
from typing import Any, Dict, List, Optional

from src.behaviour.models import PersonalisationProfile


class PersonalisationManager:
    """
    Manager for loading, updating, and applying PersonalisationProfile preferences.
    """

    def __init__(self, patient_id: str = "P1") -> None:
        self.patient_id = patient_id
        self._profile = PersonalisationProfile(patient_id=patient_id)
        self._lock = threading.Lock()

    def get_profile(self) -> PersonalisationProfile:
        with self._lock:
            return self._profile

    def update_preferred_object_location(self, object_name: str, location: str) -> None:
        with self._lock:
            obj_clean = object_name.lower().strip()
            self._profile.preferred_object_locations[obj_clean] = location

    def set_caregiver_override(self, key: str, value: Any) -> None:
        """Allow caregivers to override any personalization setting."""
        with self._lock:
            self._profile.caregiver_overrides[key] = value

    def clear_caregiver_override(self, key: str) -> None:
        with self._lock:
            if key in self._profile.caregiver_overrides:
                del self._profile.caregiver_overrides[key]

    def get_effective_setting(self, key: str, default: Any = None) -> Any:
        """Returns caregiver override if present, else standard profile value."""
        with self._lock:
            if key in self._profile.caregiver_overrides:
                return self._profile.caregiver_overrides[key]
            return getattr(self._profile, key, default)

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return self._profile.to_dict()
