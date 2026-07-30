from src.runtime.bluetooth_adapter import SimulatedBluetoothAdapter
from src.runtime.runtime_models import DeviceStatus


def test_bluetooth_adapter_scan():
    ble = SimulatedBluetoothAdapter()
    assert ble.get_status() == DeviceStatus.HEALTHY

    devices = ble.scan_devices()
    assert len(devices) >= 3
    types = [d["type"] for d in devices]
    assert "Wearable" in types
