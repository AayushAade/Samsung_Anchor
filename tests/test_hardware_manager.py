from src.runtime.hardware_manager import HardwareManager
from src.runtime.runtime_models import DeviceStatus


def test_hardware_manager_registry():
    mgr = HardwareManager()
    assert mgr.get_device_status("CameraAdapter") == DeviceStatus.HEALTHY

    mgr.register_device("CameraAdapter", DeviceStatus.FAULTED)
    assert mgr.get_device_status("CameraAdapter") == DeviceStatus.FAULTED
    assert len(mgr.get_all_statuses()) >= 6
