from src.runtime.camera_adapter import OpenCVCameraAdapter, SimulatedCameraAdapter
from src.runtime.runtime_models import DeviceStatus


def test_camera_adapter_simulation():
    cam = SimulatedCameraAdapter("Cam_0")
    assert cam.initialize() is True
    assert cam.get_status() == DeviceStatus.HEALTHY

    frame = cam.capture_frame()
    assert frame["frame_id"] == 1
    assert frame["fps"] == 30.0

    cam.shutdown()
    assert cam.get_status() == DeviceStatus.DISCONNECTED


def test_opencv_camera_adapter_interface():
    cam = OpenCVCameraAdapter(device_index=999, device_name="Test_Webcam")
    assert cam.get_status() == DeviceStatus.DISCONNECTED

    ok = cam.initialize()
    assert ok is False
    assert cam.get_status() == DeviceStatus.FAULTED

    frame = cam.capture_frame()
    assert frame["frame_id"] == 1
    assert frame["device"] == "Test_Webcam"
    assert frame["width"] == 1280
    assert frame["height"] == 720
    assert "timestamp" in frame

    cam.shutdown()
    assert cam.get_status() == DeviceStatus.DISCONNECTED
