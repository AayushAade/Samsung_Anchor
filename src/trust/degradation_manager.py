"""
MEMORA Failure Recovery & Graceful Degradation — Degradation Manager.

Monitors hardware adapter and subsystem operational health.
Executes fallback strategies when components fail (camera, microphone,
face recognition, object detection, speech synthesis) to prevent runtime crashes.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from src.trust.models import DegradationStatus, SubsystemHealthState


class DegradationManager:
    """
    Controller for subsystem failure recovery and graceful capability degradation.
    """

    def __init__(self) -> None:
        self._status = DegradationStatus()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Health Reporting & Fallback Management
    # ------------------------------------------------------------------

    def report_hardware_failure(self, component: str, error_message: str) -> DegradationStatus:
        """
        Report hardware/subsystem failure and activate appropriate fallback mode.

        Parameters
        ----------
        component : str
            E.g. ``"camera"``, ``"microphone"``, ``"face_recognition"``, ``"object_detection"``.
        error_message : str
            The diagnostic error message.

        Returns
        -------
        DegradationStatus
            Updated degradation status snapshot.
        """
        with self._lock:
            comp_lower = component.lower()

            if "camera" in comp_lower:
                self._status.camera_state = SubsystemHealthState.UNAVAILABLE
                fallback = "CAMERA_UNAVAILABLE: Operating via spatial memory cache & audio perception."
                if fallback not in self._status.active_fallbacks:
                    self._status.active_fallbacks.append(fallback)

            elif "microphone" in comp_lower or "audio" in comp_lower:
                self._status.microphone_state = SubsystemHealthState.UNAVAILABLE
                fallback = "MICROPHONE_UNAVAILABLE: Operating via camera perception & visual display cues."
                if fallback not in self._status.active_fallbacks:
                    self._status.active_fallbacks.append(fallback)

            elif "face" in comp_lower:
                self._status.face_recognition_state = SubsystemHealthState.DEGRADED
                fallback = "FACE_RECOGNITION_DEGRADED: Operating via temporal context & caregiver mode."
                if fallback not in self._status.active_fallbacks:
                    self._status.active_fallbacks.append(fallback)

            elif "object" in comp_lower:
                self._status.object_detection_state = SubsystemHealthState.DEGRADED
                fallback = "OBJECT_DETECTION_DEGRADED: Operating via visual episodic memory history."
                if fallback not in self._status.active_fallbacks:
                    self._status.active_fallbacks.append(fallback)

            elif "speaker" in comp_lower or "speech" in comp_lower:
                self._status.speech_synthesis_state = SubsystemHealthState.UNAVAILABLE
                fallback = "SPEECH_SYNTHESIS_UNAVAILABLE: Operating via visual notification cards."
                if fallback not in self._status.active_fallbacks:
                    self._status.active_fallbacks.append(fallback)

            # Update overall health status
            unavail_count = sum(
                1 for s in (
                    self._status.camera_state,
                    self._status.microphone_state,
                    self._status.face_recognition_state,
                    self._status.object_detection_state,
                    self._status.speech_synthesis_state,
                ) if s != SubsystemHealthState.FULL
            )

            if unavail_count == 0:
                self._status.overall_health = "HEALTHY"
            elif unavail_count <= 2:
                self._status.overall_health = "DEGRADED"
            else:
                self._status.overall_health = "CRITICAL_DEGRADED"

            print(f"[DegradationManager] Component '{component}' failure reported: {error_message}. Mode: {self._status.overall_health}")
            return self._status

    def recover_hardware(self, component: str) -> DegradationStatus:
        """Mark a component as recovered and clear fallbacks."""
        with self._lock:
            comp_lower = component.lower()
            if "camera" in comp_lower:
                self._status.camera_state = SubsystemHealthState.FULL
            elif "microphone" in comp_lower or "audio" in comp_lower:
                self._status.microphone_state = SubsystemHealthState.FULL
            elif "face" in comp_lower:
                self._status.face_recognition_state = SubsystemHealthState.FULL
            elif "object" in comp_lower:
                self._status.object_detection_state = SubsystemHealthState.FULL
            elif "speaker" in comp_lower or "speech" in comp_lower:
                self._status.speech_synthesis_state = SubsystemHealthState.FULL

            # Filter active fallbacks
            self._status.active_fallbacks = [
                f for f in self._status.active_fallbacks if component.upper() not in f
            ]

            unavail = sum(
                1 for s in (
                    self._status.camera_state,
                    self._status.microphone_state,
                    self._status.face_recognition_state,
                    self._status.object_detection_state,
                    self._status.speech_synthesis_state,
                ) if s != SubsystemHealthState.FULL
            )
            self._status.overall_health = "HEALTHY" if unavail == 0 else "DEGRADED"

            return self._status

    def get_status(self) -> DegradationStatus:
        with self._lock:
            return self._status

    def reset(self) -> None:
        with self._lock:
            self._status = DegradationStatus()
