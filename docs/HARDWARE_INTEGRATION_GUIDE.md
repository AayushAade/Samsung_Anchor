# Memora Hardware Integration & HAL Guide

## Hardware Abstraction Layer (HAL)
Memora interacts with hardware sensors exclusively through dependency-injected adapters in `src/runtime/`:

- **`CameraAdapter` (`camera_adapter.py`)**: Inherit from `CameraAdapter` to add physical USB, OpenCV, V4L2, PiCamera, or Jetson CSI camera drivers.
- **`MicrophoneAdapter` (`microphone_adapter.py`)**: Inherit from `MicrophoneAdapter` to integrate PortAudio, PyAudio, or ALSA audio streams.
- **`SpeakerAdapter` (`speaker_adapter.py`)**: Inherit from `SpeakerAdapter` for native Text-To-Speech (TTS), chime sound files, or hardware alarm sirens.
- **`BluetoothAdapter` (`bluetooth_adapter.py`)**: Inherit from `BluetoothAdapter` for BlueZ, Bleak, or WebBluetooth wearable and beacon scanners.
- **`IMUAdapter` (`imu_adapter.py`)**: Inherit from `IMUAdapter` for MPU6050, LSM6DS3, or accelerometer fall sensors.

## SensorBus Event Publishing
Adapters publish events to `SensorBus`:
```python
from src.runtime.sensor_bus import SensorBus
from src.runtime.runtime_models import SensorEvent, SensorEventType

bus = SensorBus()
bus.publish(SensorEvent(event_type=SensorEventType.CAMERA_FRAME, source_device="Custom_Webcam"))
```
