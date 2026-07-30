"""
MEMORA Unified Cognitive Subsystem Interface.

Defines the standard ICognitiveSubsystem abstract base class enforcing consistent
lifecycle management, health monitoring, metrics instrumentation, and explainability across all cognitive layers:
- Cognitive Operating System (Phase 21)
- Trust & Safety Framework (Phase 22)
- Behaviour Intelligence Platform (Phase 23)
- Cognitive Reasoning Engine (Phase 24)
- Executive Function Framework (Phase 25)
- Experience Learning Framework (Phase 26)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ICognitiveSubsystem(ABC):
    """
    Standard interface for all MEMORA cognitive subsystems.
    """

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize subsystem resources, databases, and background listeners.
        """
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """
        Safely shut down subsystem, flushing memory and releasing locks.
        """
        pass

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute one cycle of processing for the subsystem.
        """
        pass

    @abstractmethod
    def status(self) -> str:
        """
        Return high-level operational status ("INITIALIZED", "RUNNING", "DEGRADED", "SHUTDOWN").
        """
        pass

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """
        Return structured health diagnostic dictionary.
        """
        pass

    @abstractmethod
    def metrics(self) -> Dict[str, Any]:
        """
        Return subsystem performance and throughput metrics.
        """
        pass

    @abstractmethod
    def explain(self) -> str:
        """
        Return human-readable explanation of recent subsystem decisions.
        """
        pass
