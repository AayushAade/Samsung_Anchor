from src.runtime.microphone_adapter import SimulatedMicrophoneAdapter
from src.runtime.runtime_models import DeviceStatus


def test_microphone_adapter_simulation():
    mic = SimulatedMicrophoneAdapter("Mic_0")
    assert mic.initialize() is True
    assert mic.get_status() == DeviceStatus.HEALTHY

    chunk = mic.read_chunk()
    assert chunk["chunk_id"] == 1
    assert chunk["sample_rate"] == 16000

    mic.shutdown()
    assert mic.get_status() == DeviceStatus.DISCONNECTED
