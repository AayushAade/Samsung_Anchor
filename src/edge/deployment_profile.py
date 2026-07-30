"""
MEMORA Declarative Deployment Profiles.

Defines hardware-independent deployment profiles for Smartphones, Smartwatches, Smart Glasses,
and Offline Clinical Edge hardware.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from src.edge.edge_models import Capability


# Declarative deployment capability matrices
DEPLOYMENT_PROFILES: Dict[str, List[Capability]] = {
    "SMARTPHONE": [
        Capability.CAMERA,
        Capability.MICROPHONE,
        Capability.SPEAKER,
        Capability.DISPLAY,
        Capability.STORAGE,
        Capability.NETWORK,
        Capability.GPS,
    ],
    "SMARTWATCH": [
        Capability.MICROPHONE,
        Capability.SPEAKER,
        Capability.HAPTIC,
        Capability.DISPLAY,
        Capability.STORAGE,
    ],
    "SMART_GLASSES": [
        Capability.CAMERA,
        Capability.MICROPHONE,
        Capability.SPEAKER,
        Capability.DISPLAY,
        Capability.STORAGE,
    ],
    "OFFLINE_CLINICAL": [
        Capability.CAMERA,
        Capability.MICROPHONE,
        Capability.SPEAKER,
        Capability.DISPLAY,
        Capability.STORAGE,
    ],
}


class DeploymentProfileManager:
    """
    Declarative manager for pre-configured deployment profiles.
    Maps hardware form-factors to abstract capability arrays.
    """

    @classmethod
    def get_profile(cls, name: str) -> List[Capability]:
        """
        Return capabilities list for named deployment profile.
        Defaults to SMARTPHONE profile if unrecognized.
        """
        name_upper = name.upper()
        return list(DEPLOYMENT_PROFILES.get(name_upper, DEPLOYMENT_PROFILES["SMARTPHONE"]))

    @classmethod
    def is_valid_profile(cls, name: str) -> bool:
        """Return True if name matches a registered deployment profile."""
        return name.upper() in DEPLOYMENT_PROFILES

    @classmethod
    def get_profile_summary(cls, name: str) -> str:
        """Return a human-readable summary of a profile's active capabilities."""
        caps = cls.get_profile(name)
        cap_names = ", ".join([c.value for c in caps])
        return f"Deployment Profile [{name.upper()}]: Active capabilities -> {cap_names}"

    @classmethod
    def has_vision(cls, name: str) -> bool:
        """Return True if specified profile includes CAMERA capability."""
        return Capability.CAMERA in cls.get_profile(name)

    @classmethod
    def has_haptic(cls, name: str) -> bool:
        """Return True if specified profile includes HAPTIC capability."""
        return Capability.HAPTIC in cls.get_profile(name)

    @classmethod
    def list_profiles(cls) -> List[str]:
        """
        Return names of all supported deployment profiles.
        """
        return list(DEPLOYMENT_PROFILES.keys())
