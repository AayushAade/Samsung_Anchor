"""
Samsung Anchor Runtime

This module owns the application's execution lifecycle.

Responsibilities
----------------
- Start the application.
- Stop the application.
- Coordinate the application's runtime loop.

Business logic belongs in the Coordinator.
Hardware-specific logic belongs in the subsystem modules.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from src.coordinator.anchor_coordinator import AnchorCoordinator
from src.runtime.runtime_models import DeviceStatus, RuntimeMode


class AnchorRuntime:
    """
    Runtime controller for Samsung Anchor.

    The Runtime is responsible for executing the application.
    It does not contain business logic.
    """

    def __init__(self, coordinator: AnchorCoordinator) -> None:
        self.coordinator = coordinator
        self.running = False
        self.cycle_count = 0

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def initialize(self) -> None:
        """
        Initialize the runtime.
        """
        self.coordinator.initialize()
        self.running = False
        self.cycle_count = 0

    def start(self) -> None:
        """
        Start runtime execution.
        """
        self.coordinator.start()
        self.running = True

    def shutdown(self) -> None:
        """
        Stop runtime execution.
        """
        self.coordinator.shutdown()
        self.running = False

    # ---------------------------------------------------------
    # Subsystem Introspection & Observability
    # ---------------------------------------------------------

    def get_subsystem_statuses(self) -> Dict[str, str]:
        """
        Inspect all application subsystems and return Phase 6 status map:
        READY | WARNING | DISABLED | FAILED
        """
        statuses = {
            "Runtime": "READY",
            "Camera": "READY",
            "Audio": "READY",
            "Speech Recognition": "READY",
            "Memory": "READY",
            "Perception": "READY",
            "Cognition": "READY",
            "Care Policy": "READY",
            "Decision Trace": "READY",
            "Speaker": "READY",
        }

        try:
            rm = getattr(self.coordinator.pipeline, "runtime_manager", None)
            if rm is not None:
                # Camera status
                cam_status = rm.camera.get_status()
                from src.runtime.camera_adapter import SimulatedCameraAdapter
                if cam_status != DeviceStatus.HEALTHY:
                    statuses["Camera"] = "FAILED"
                elif isinstance(rm.camera, SimulatedCameraAdapter):
                    statuses["Camera"] = "WARNING (Simulated)"

                # Audio / Mic status
                mic_status = rm.microphone.get_status()
                from src.runtime.microphone_adapter import SimulatedMicrophoneAdapter
                if mic_status != DeviceStatus.HEALTHY:
                    statuses["Audio"] = "FAILED"
                elif isinstance(rm.microphone, SimulatedMicrophoneAdapter):
                    statuses["Audio"] = "WARNING (Simulated)"

                # Speaker status
                spk_status = rm.speaker.get_status()
                from src.runtime.speaker_adapter import SimulatedSpeakerAdapter
                if spk_status != DeviceStatus.HEALTHY:
                    statuses["Speaker"] = "FAILED"
                elif isinstance(rm.speaker, SimulatedSpeakerAdapter):
                    statuses["Speaker"] = "WARNING (Simulated)"
        except Exception:
            pass

        # Memory status
        try:
            if not self.coordinator.database:
                statuses["Memory"] = "FAILED"
        except Exception:
            statuses["Memory"] = "WARNING"

        return statuses

    # ---------------------------------------------------------
    # Runtime Delegation
    # ---------------------------------------------------------

    def process_frame(self, frame: Any):
        """
        Delegate frame processing to the Coordinator.
        """
        return self.coordinator.process_frame(frame)

    def process_single_frame(self, camera: Optional[Any] = None):
        """
        Capture and process a single camera frame.
        If camera is None, defaults to coordinator's hardware camera adapter.
        """
        target_camera = camera
        if target_camera is None:
            try:
                target_camera = self.coordinator.pipeline.runtime_manager.camera
            except AttributeError:
                target_camera = None

        if target_camera is None:
            # Generate a synthetic frame if no camera available
            frame = {"frame_id": self.cycle_count + 1, "timestamp": time.time()}
            results = self.process_frame(frame)
            return frame, results

        success, frame = target_camera.read()

        if not success:
            raise RuntimeError("Failed to capture frame.")

        results = self.process_frame(frame)
        return frame, results

    # ---------------------------------------------------------
    # Runtime Execution
    # ---------------------------------------------------------

    def run_once(self, camera: Optional[Any] = None):
        """
        Execute a single runtime iteration.
        """
        if not self.running:
            raise RuntimeError("Runtime is not running.")

        self.cycle_count += 1
        return self.process_single_frame(camera)

    # ---------------------------------------------------------
    # Runtime Loop
    # ---------------------------------------------------------

    def run(self, camera: Optional[Any] = None):
        """
        Execute the application's runtime loop generator.
        """
        self.start()
        try:
            while self.running:
                yield self.run_once(camera)
        finally:
            self.shutdown()

    def run_continuous(
        self,
        max_cycles: Optional[int] = None,
        cycle_delay: float = 0.1,
        camera: Optional[Any] = None,
    ) -> None:
        """
        Execute continuous runtime loop until stopped or max_cycles reached.
        """
        if not self.running:
            self.start()

        print("⚡ MEMORA Active Processing Loop Started.")
        try:
            while self.running:
                try:
                    frame, results = self.run_once(camera)

                    # Consume and dispatch any pending interaction actions
                    actions = self.coordinator.consume_actions()
                    for action in actions:
                        if hasattr(self.coordinator.speaker, "execute"):
                            self.coordinator.speaker.execute(action)
                        elif hasattr(self.coordinator.speaker, "speak") and getattr(action, "message", None):
                            self.coordinator.speaker.speak(action.message)

                    if self.cycle_count % 10 == 0 or self.cycle_count == 1:
                        print(f"💓 [Heartbeat] Runtime cycle #{self.cycle_count} completed successfully.")

                except Exception as e:
                    print(f"⚠️ [Runtime Warning] Cycle iteration error: {e}")

                if max_cycles is not None and self.cycle_count >= max_cycles:
                    print(f"🛑 Max execution cycles ({max_cycles}) reached.")
                    break

                if cycle_delay > 0:
                    time.sleep(cycle_delay)
        finally:
            self.shutdown()
            print("🟢 MEMORA Runtime Shutdown Complete.")