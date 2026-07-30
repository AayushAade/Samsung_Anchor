from src.runtime.microphone_adapter import PyAudioMicrophoneAdapter, SimulatedMicrophoneAdapter
from src.runtime.runtime_models import DeviceStatus, HardwareConfig, RuntimeMode, SensorEventType
from src.runtime.runtime_manager import RuntimeManager
from src.perception.audio_pipeline import AudioPipeline
from src.runtime.sensor_bus import SensorBus


def test_microphone_adapter_simulation():
    mic = SimulatedMicrophoneAdapter("Mic_0")
    assert mic.initialize() is True
    assert mic.get_status() == DeviceStatus.HEALTHY

    chunk = mic.read_chunk()
    assert chunk["chunk_id"] == 1
    assert chunk["sample_rate"] == 16000

    mic.shutdown()
    assert mic.get_status() == DeviceStatus.DISCONNECTED


def test_pyaudio_microphone_adapter_interface():
    mic = PyAudioMicrophoneAdapter(sample_rate=16000, chunk_size=1024, device_name="Test_Mic")
    assert mic.get_status() == DeviceStatus.DISCONNECTED

    ok = mic.initialize()
    if ok:
        assert mic.get_status() == DeviceStatus.HEALTHY
        chunk = mic.read_chunk()
        assert chunk["chunk_id"] == 1
        assert chunk["device"] == "Test_Mic"
        assert chunk["sample_rate"] == 16000
        assert chunk["channels"] == 1
        assert "timestamp" in chunk
        mic.shutdown()
        assert mic.get_status() == DeviceStatus.DISCONNECTED
    else:
        assert mic.get_status() == DeviceStatus.FAULTED
        mic.shutdown()


def test_runtime_manager_microphone_adapter_selection():
    config_sim = HardwareConfig(mode=RuntimeMode.SIMULATION)
    rm_sim = RuntimeManager(config=config_sim)
    assert isinstance(rm_sim.microphone, SimulatedMicrophoneAdapter)
    rm_sim.shutdown_hardware()

    config_laptop = HardwareConfig(mode=RuntimeMode.LAPTOP)
    rm_laptop = RuntimeManager(config=config_laptop)
    assert isinstance(rm_laptop.microphone, (PyAudioMicrophoneAdapter, SimulatedMicrophoneAdapter))
    rm_laptop.shutdown_hardware()


def test_audio_pipeline_microphone_integration():
    bus = SensorBus()
    mic = SimulatedMicrophoneAdapter("TestMic")
    mic.initialize()

    received_events = []
    bus.subscribe(SensorEventType.AUDIO_EVENT, lambda e: received_events.append(e))

    pipeline = AudioPipeline(microphone_adapter=mic, sensor_bus=bus)
    chunk = pipeline.process_audio_chunk()

    assert chunk is not None
    assert len(received_events) == 1
    assert received_events[0].event_type == SensorEventType.AUDIO_EVENT
    assert received_events[0].source_device == "TestMic"
    mic.shutdown()
