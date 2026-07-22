from abc import ABC, abstractmethod
from src.runtime.runtime_models import DeviceStatus


class DisplayAdapter(ABC):
    """
    Abstract Display & Indicator Hardware Adapter.
    """

    @abstractmethod
    def show_message(self, message: str) -> bool:
        pass

    @abstractmethod
    def set_led_status(self, color: str) -> bool:
        pass

    @abstractmethod
    def get_status(self) -> DeviceStatus:
        pass


class SimulatedDisplayAdapter(DisplayAdapter):
    """
    Simulated Display Adapter.
    """

    def __init__(self, device_name: str = "Simulated_Display_0") -> None:
        self.device_name = device_name
        self.status = DeviceStatus.HEALTHY
        self.current_led = "GREEN"

    def show_message(self, message: str) -> bool:
        print(f"[SimulatedDisplay] Render: '{message}'")
        return True

    def set_led_status(self, color: str) -> bool:
        self.current_led = color.upper()
        print(f"[SimulatedDisplay] LED Status -> {self.current_led}")
        return True

    def get_status(self) -> DeviceStatus:
        return self.status
