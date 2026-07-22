from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.runtime.runtime_models import DeviceStatus


class BluetoothAdapter(ABC):
    """
    Abstract Bluetooth BLE Hardware Adapter.
    """

    @abstractmethod
    def scan_devices(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_status(self) -> DeviceStatus:
        pass


class SimulatedBluetoothAdapter(BluetoothAdapter):
    """
    Simulated BLE Adapter.
    """

    def __init__(self, device_name: str = "Simulated_BLE_0") -> None:
        self.device_name = device_name
        self.status = DeviceStatus.HEALTHY

    def scan_devices(self) -> List[Dict[str, Any]]:
        return [
            {"device_id": "BLE-WATCH-01", "name": "Galaxy Smart Watch", "rssi": -55, "type": "Wearable"},
            {"device_id": "BLE-BEACON-02", "name": "Living Room Beacon", "rssi": -42, "type": "Location Beacon"},
            {"device_id": "BLE-MED-03", "name": "Smart Pill Dispenser", "rssi": -60, "type": "Medical Device"},
        ]

    def get_status(self) -> DeviceStatus:
        return self.status
