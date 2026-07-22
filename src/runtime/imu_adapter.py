from abc import ABC, abstractmethod
from typing import Dict, Any
from src.runtime.runtime_models import DeviceStatus


class IMUAdapter(ABC):
    """
    Abstract Inertial Measurement Unit (IMU) Motion & Fall Sensor Adapter.
    """

    @abstractmethod
    def read_motion(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_status(self) -> DeviceStatus:
        pass


class SimulatedIMUAdapter(IMUAdapter):
    """
    Simulated IMU Motion & Accelerometer Adapter.
    """

    def __init__(self, device_name: str = "Simulated_IMU_0") -> None:
        self.device_name = device_name
        self.status = DeviceStatus.HEALTHY

    def read_motion(self) -> Dict[str, Any]:
        return {
            "device": self.device_name,
            "accel_g": [0.01, 0.02, 0.98],
            "gyro_dps": [0.1, 0.0, -0.1],
            "motion_detected": True,
            "fall_impact_detected": False,
        }

    def get_status(self) -> DeviceStatus:
        return self.status
