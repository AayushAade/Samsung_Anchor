from typing import Dict
from src.runtime.runtime_models import DeviceStatus


class HardwareManager:
    """
    Hardware Device Registry and Connectivity Tracker.
    """

    def __init__(self) -> None:
        self._devices: Dict[str, DeviceStatus] = {
            "CameraAdapter": DeviceStatus.HEALTHY,
            "MicrophoneAdapter": DeviceStatus.HEALTHY,
            "SpeakerAdapter": DeviceStatus.HEALTHY,
            "DisplayAdapter": DeviceStatus.HEALTHY,
            "BluetoothAdapter": DeviceStatus.HEALTHY,
            "IMUAdapter": DeviceStatus.HEALTHY,
        }

    def register_device(self, device_name: str, status: DeviceStatus) -> None:
        self._devices[device_name] = status

    def get_device_status(self, device_name: str) -> DeviceStatus:
        return self._devices.get(device_name, DeviceStatus.DISCONNECTED)

    def get_all_statuses(self) -> Dict[str, str]:
        return {name: status.value for name, status in self._devices.items()}
