from abc import ABC, abstractmethod
from src.runtime.runtime_models import DeviceStatus


class SpeakerAdapter(ABC):
    """
    Abstract Speaker Hardware Adapter.
    """

    @abstractmethod
    def speak(self, text: str) -> bool:
        pass

    @abstractmethod
    def play_chime(self) -> bool:
        pass

    @abstractmethod
    def trigger_alarm(self) -> bool:
        pass

    @abstractmethod
    def set_volume(self, volume_pct: float) -> float:
        pass

    @abstractmethod
    def get_status(self) -> DeviceStatus:
        pass


class SimulatedSpeakerAdapter(SpeakerAdapter):
    """
    Simulated Speaker Adapter.
    """

    def __init__(self, device_name: str = "Simulated_Speaker_0") -> None:
        self.device_name = device_name
        self.status = DeviceStatus.HEALTHY
        self.volume = 80.0

    def speak(self, text: str) -> bool:
        print(f"[SimulatedSpeaker] Speaking: '{text}' (Vol: {self.volume}%)")
        return True

    def play_chime(self) -> bool:
        print(f"[SimulatedSpeaker] Play Chime (Vol: {self.volume}%)")
        return True

    def trigger_alarm(self) -> bool:
        print(f"[SimulatedSpeaker] TRIGGER ALARM (Vol: 100%)")
        return True

    def set_volume(self, volume_pct: float) -> float:
        self.volume = max(0.0, min(100.0, volume_pct))
        return self.volume

    def get_status(self) -> DeviceStatus:
        return self.status
