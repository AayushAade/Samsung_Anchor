"""
Samsung Anchor Camera Device

Hardware abstraction for camera access.

Responsibilities
----------------
- Open the camera.
- Read frames.
- Release camera resources.

This module hides OpenCV-specific details from the Runtime.
"""

from __future__ import annotations

import cv2


class CameraDevice:
    """
    Hardware abstraction around OpenCV's VideoCapture.
    """

    def __init__(self, camera_index: int = 0) -> None:
        self.camera_index = camera_index
        self.capture = None

    def open(self) -> bool:
        """
        Open the camera.

        Returns
        -------
        bool
            True if the camera opened successfully.
        """

        self.capture = cv2.VideoCapture(self.camera_index)
        return self.capture.isOpened()

    def is_open(self) -> bool:
        """
        Return whether the camera is currently open.
        """

        return (
            self.capture is not None
            and self.capture.isOpened()
        )

    def read(self):
        """
        Read one frame from the camera.

        Returns
        -------
        (success, frame)
        """

        if not self.is_open():
            return False, None

        return self.capture.read()

    def release(self) -> None:
        """
        Release the camera.
        """

        if self.capture is not None:
            self.capture.release()
            self.capture = None