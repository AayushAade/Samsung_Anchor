from abc import ABC, abstractmethod
from typing import Dict, Any
from src.runtime.runtime_models import DeviceStatus


class CameraAdapter(ABC):
    """
    Abstract Camera Hardware Adapter.
    """

    @abstractmethod
    def initialize(self) -> bool:
        pass

    @abstractmethod
    def capture_frame(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_status(self) -> DeviceStatus:
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass


class SimulatedCameraAdapter(CameraAdapter):
    """
    Simulated Camera Adapter for software verification and desktop testing.
    """

    def __init__(self, device_name: str = "Simulated_Camera_0") -> None:
        self.device_name = device_name
        self.status = DeviceStatus.DISCONNECTED
        self.frame_count = 0

    def initialize(self) -> bool:
        self.status = DeviceStatus.HEALTHY
        return True

    def capture_frame(self) -> Dict[str, Any]:
        self.frame_count += 1
        return {
            "frame_id": self.frame_count,
            "device": self.device_name,
            "width": 1280,
            "height": 720,
            "fps": 30.0,
        }

    def get_status(self) -> DeviceStatus:
        return self.status

    def shutdown(self) -> None:
        self.status = DeviceStatus.DISCONNECTED
