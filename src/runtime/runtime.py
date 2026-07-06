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

from typing import Any

from src.coordinator.anchor_coordinator import AnchorCoordinator


class AnchorRuntime:
    """
    Runtime controller for Samsung Anchor.

    The Runtime is responsible for executing the application.
    It does not contain business logic.
    """

    def __init__(self, coordinator: AnchorCoordinator) -> None:
        self.coordinator = coordinator
        self.running = False

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def initialize(self) -> None:
        """
        Initialize the runtime.
        """
        self.coordinator.initialize()
        self.running = False

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
    # Runtime Delegation
    # ---------------------------------------------------------

    def process_frame(self, frame: Any):
        """
        Delegate frame processing to the Coordinator.

        The Runtime owns execution.
        The Coordinator owns application logic.
        """
        return self.coordinator.process_frame(frame)

    def process_single_frame(self, camera):
        """
        Capture and process a single camera frame.

        Parameters
        ----------
        camera
            An already-open camera object exposing a read() method.

        Returns
        -------
        tuple
            (frame, results)

        Raises
        ------
        RuntimeError
            If the camera fails to capture a frame.
        """

        success, frame = camera.read()

        if not success:
            raise RuntimeError("Failed to capture frame.")

        results = self.process_frame(frame)

        return frame, results