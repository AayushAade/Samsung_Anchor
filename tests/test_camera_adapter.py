from src.runtime.camera_adapter import SimulatedCameraAdapter
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
