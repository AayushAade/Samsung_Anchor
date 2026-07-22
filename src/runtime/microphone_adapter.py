from abc import ABC, abstractmethod
from typing import Dict, Any
from src.runtime.runtime_models import DeviceStatus


class MicrophoneAdapter(ABC):
    """
    Abstract Microphone Hardware Adapter.
    """

    @abstractmethod
    def initialize(self) -> bool:
        pass

    @abstractmethod
    def read_chunk(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_status(self) -> DeviceStatus:
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass


class SimulatedMicrophoneAdapter(MicrophoneAdapter):
    """
    Simulated Microphone Adapter.
    """

    def __init__(self, device_name: str = "Simulated_Mic_0") -> None:
        self.device_name = device_name
        self.status = DeviceStatus.DISCONNECTED
        self.sample_counter = 0

    def initialize(self) -> bool:
        self.status = DeviceStatus.HEALTHY
        return True

    def read_chunk(self) -> Dict[str, Any]:
        self.sample_counter += 1
        return {
            "chunk_id": self.sample_counter,
            "device": self.device_name,
            "sample_rate": 16000,
            "channels": 1,
            "latency_ms": 12.5,
        }

    def get_status(self) -> DeviceStatus:
        return self.status

    def shutdown(self) -> None:
        self.status = DeviceStatus.DISCONNECTED
