from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class RuntimeMode(Enum):
    SIMULATION = "Simulation Mode"
    LAPTOP = "Laptop Dev Mode"
    RASPBERRY_PI = "Raspberry Pi Mode"
    JETSON = "NVIDIA Jetson Mode"
    PRODUCTION = "Production Edge Mode"


class DeviceStatus(Enum):
    CONNECTED = "Connected"
    DISCONNECTED = "Disconnected"
    HEALTHY = "Healthy"
    FAULTED = "Faulted"
    RESTARTING = "Restarting"
    DISABLED = "Disabled"


class SensorEventType(Enum):
    CAMERA_FRAME = "Camera Frame"
    AUDIO_EVENT = "Audio Event"
    SPEECH_TRANSCRIPT = "Speech Transcript"
    BLE_BEACON = "BLE Beacon"
    IMU_MOTION = "IMU Motion"
    HEALTH_TELEMETRY = "Health Telemetry"


@dataclass
class HardwareConfig:
    mode: RuntimeMode = RuntimeMode.SIMULATION
    camera_device: str = "Virtual_Webcam_0"
    audio_input_device: str = "Default_Mic"
    audio_output_device: str = "Default_Speaker"
    enable_ble: bool = True
    enable_imu: bool = True


@dataclass
class HealthMetrics:
    # Zero means "not measured"; see metrics_measured. (Defaults used to be
    # plausible-looking constants that could be mistaken for measurements.)
    cpu_usage_pct: float = 0.0
    ram_usage_pct: float = 0.0
    camera_fps: float = 0.0
    audio_latency_ms: float = 0.0
    connected_devices_count: int = 0
    metrics_measured: bool = False


@dataclass
class SensorEvent:
    event_type: SensorEventType
    source_device: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
