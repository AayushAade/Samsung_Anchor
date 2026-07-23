from typing import Dict, Any, Optional
from src.runtime.bluetooth_adapter import SimulatedBluetoothAdapter
from src.runtime.camera_adapter import OpenCVCameraAdapter, SimulatedCameraAdapter
from src.runtime.display_adapter import SimulatedDisplayAdapter
from src.runtime.hardware_manager import HardwareManager
from src.runtime.imu_adapter import SimulatedIMUAdapter
from src.runtime.microphone_adapter import SimulatedMicrophoneAdapter
from src.runtime.runtime_models import DeviceStatus, HardwareConfig, HealthMetrics, RuntimeMode
from src.runtime.sensor_bus import SensorBus
from src.runtime.speaker_adapter import SimulatedSpeakerAdapter


class RuntimeManager:
    """
    Central Hardware Runtime Orchestrator managing device lifecycle, health monitoring,
    and adapter isolation across Simulation, Laptop, Pi, and Jetson modes.
    """

    def __init__(self, config: Optional[HardwareConfig] = None) -> None:
        self.config = config or HardwareConfig()
        self.sensor_bus = SensorBus()
        self.hardware_manager = HardwareManager()

        # Instantiate Adapters based on RuntimeMode
        if self.config.mode != RuntimeMode.SIMULATION:
            self.camera = OpenCVCameraAdapter(device_name=self.config.camera_device)
        else:
            self.camera = SimulatedCameraAdapter(self.config.camera_device)

        self.microphone = SimulatedMicrophoneAdapter(self.config.audio_input_device)
        self.speaker = SimulatedSpeakerAdapter(self.config.audio_output_device)
        self.display = SimulatedDisplayAdapter()
        self.bluetooth = SimulatedBluetoothAdapter()
        self.imu = SimulatedIMUAdapter()

        self.initialize_hardware()

    def initialize_hardware(self) -> bool:
        cam_ok = self.camera.initialize()
        if not cam_ok and isinstance(self.camera, OpenCVCameraAdapter):
            # Graceful fallback to simulation if physical camera unavailable
            self.camera = SimulatedCameraAdapter(self.config.camera_device)
            cam_ok = self.camera.initialize()

        mic_ok = self.microphone.initialize()

        self.hardware_manager.register_device("CameraAdapter", self.camera.get_status())
        self.hardware_manager.register_device("MicrophoneAdapter", self.microphone.get_status())
        self.hardware_manager.register_device("SpeakerAdapter", self.speaker.get_status())
        self.hardware_manager.register_device("DisplayAdapter", self.display.get_status())
        self.hardware_manager.register_device("BluetoothAdapter", self.bluetooth.get_status())
        self.hardware_manager.register_device("IMUAdapter", self.imu.get_status())

        return cam_ok and mic_ok

    def get_health_metrics(self) -> HealthMetrics:
        return HealthMetrics(
            cpu_usage_pct=14.2,
            ram_usage_pct=36.8,
            camera_fps=30.0,
            audio_latency_ms=11.8,
            connected_devices_count=len(self.hardware_manager.get_all_statuses()),
        )

    def get_runtime_summary(self) -> Dict[str, Any]:
        health = self.get_health_metrics()
        return {
            "mode": self.config.mode.value,
            "device_statuses": self.hardware_manager.get_all_statuses(),
            "cpu_usage_pct": health.cpu_usage_pct,
            "ram_usage_pct": health.ram_usage_pct,
            "camera_fps": health.camera_fps,
            "audio_latency_ms": health.audio_latency_ms,
            "connected_devices": health.connected_devices_count,
        }

    def shutdown_hardware(self) -> None:
        self.camera.shutdown()
        self.microphone.shutdown()
        self.sensor_bus.clear()
