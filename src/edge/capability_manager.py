"""
MEMORA Capability Manager.

Manages abstract hardware capability availability (Camera, Speaker, Storage, GPS, Network)
without making platform SDK or driver calls.
"""

from __future__ import annotations

import threading
from typing import List, Set

from src.edge.edge_models import Capability


class CapabilityManager:
    """
    Thread-safe abstract capability availability manager.
    Coordinates active capability flags across edge execution cycles.
    """

    def __init__(self) -> None:
        self._active_capabilities: Set[Capability] = {
            Capability.CAMERA,
            Capability.MICROPHONE,
            Capability.SPEAKER,
            Capability.DISPLAY,
            Capability.STORAGE,
            Capability.NETWORK,
        }
        self._lock = threading.Lock()

    def enable_capability(self, capability: Capability) -> None:
        """Enable an abstract capability flag."""
        with self._lock:
            self._active_capabilities.add(capability)

    def disable_capability(self, capability: Capability) -> None:
        """Disable an abstract capability flag."""
        with self._lock:
            self._active_capabilities.discard(capability)

    def is_available(self, capability: Capability) -> bool:
        """Check if an abstract capability is currently active and available."""
        with self._lock:
            return capability in self._active_capabilities

    def get_active_capabilities(self) -> List[Capability]:
        """Return list of currently active capabilities."""
        with self._lock:
            return list(self._active_capabilities)

    def set_active_capabilities(self, capabilities: List[Capability]) -> None:
        """Overwrites active capabilities list."""
        with self._lock:
            self._active_capabilities = set(capabilities)

    def get_essential_capabilities(self) -> List[Capability]:
        """Return subset of active capabilities that are classified as essential."""
        with self._lock:
            return [c for c in self._active_capabilities if c.is_essential()]

    def has_vision_capability(self) -> bool:
        """Return True if CAMERA capability is active."""
        return self.is_available(Capability.CAMERA)

    def has_audio_capability(self) -> bool:
        """Return True if MICROPHONE or SPEAKER capability is active."""
        with self._lock:
            return Capability.MICROPHONE in self._active_capabilities or Capability.SPEAKER in self._active_capabilities

    def clear(self) -> None:
        """Reset capabilities to empty."""
        with self._lock:
            self._active_capabilities.clear()
