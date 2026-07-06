"""
Unit tests for CameraDevice.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

from devices.camera import CameraDevice


@patch("devices.camera.cv2.VideoCapture")
def test_open(mock_capture):

    fake_capture = MagicMock()
    fake_capture.isOpened.return_value = True

    mock_capture.return_value = fake_capture

    camera = CameraDevice()

    assert camera.open() is True
    assert camera.is_open() is True


@patch("devices.camera.cv2.VideoCapture")
def test_read(mock_capture):

    fake_capture = MagicMock()
    fake_capture.isOpened.return_value = True
    fake_capture.read.return_value = (True, "FRAME")

    mock_capture.return_value = fake_capture

    camera = CameraDevice()

    camera.open()

    success, frame = camera.read()

    assert success is True
    assert frame == "FRAME"


@patch("devices.camera.cv2.VideoCapture")
def test_release(mock_capture):

    fake_capture = MagicMock()
    fake_capture.isOpened.return_value = True

    mock_capture.return_value = fake_capture

    camera = CameraDevice()

    camera.open()
    camera.release()

    fake_capture.release.assert_called_once()
    assert camera.capture is None


def test_read_without_open():

    camera = CameraDevice()

    success, frame = camera.read()

    assert success is False
    assert frame is None