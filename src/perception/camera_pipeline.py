from typing import Optional, Any
import time
from datetime import datetime
from src.perception.sensor_models import FrameData


class CameraPipeline:
    """
    Modular video frame acquisition and synchronization pipeline.
    Connects to Hardware Abstraction Layer (HAL) CameraAdapter and SensorBus.
    """

    def __init__(
        self,
        target_fps: float = 30.0,
        camera_adapter: Optional[Any] = None,
        sensor_bus: Optional[Any] = None,
    ) -> None:
        self.target_fps = target_fps
        self.camera_adapter = camera_adapter
        self.sensor_bus = sensor_bus
        self._frame_counter = 0
        self._last_time = time.perf_counter()

    def set_camera_adapter(self, adapter: Any) -> None:
        self.camera_adapter = adapter

    def set_sensor_bus(self, bus: Any) -> None:
        self.sensor_bus = bus

    def acquire_frame(self) -> FrameData:
        self._frame_counter += 1
        now = time.perf_counter()
        elapsed = now - self._last_time
        self._last_time = now
        fps = round(1.0 / max(elapsed, 0.001), 1)

        raw_frame = None
        width = 1280
        height = 720

        if self.camera_adapter is not None:
            frame_data = self.camera_adapter.capture_frame()
            width = frame_data.get("width", 1280)
            height = frame_data.get("height", 720)
            raw_frame = frame_data.get("raw_frame")
            if "fps" in frame_data and frame_data["fps"] > 0:
                fps = frame_data["fps"]

            if self.sensor_bus is not None:
                from src.runtime.runtime_models import SensorEvent, SensorEventType
                event = SensorEvent(
                    event_type=SensorEventType.CAMERA_FRAME,
                    source_device=getattr(self.camera_adapter, "device_name", "CameraAdapter"),
                    data=frame_data,
                )
                self.sensor_bus.publish(event)

        return FrameData(
            frame_id=self._frame_counter,
            timestamp=datetime.now().isoformat(),
            width=width,
            height=height,
            fps=min(fps, self.target_fps) if fps > 0 else self.target_fps,
            raw_frame=raw_frame,
        )

    def get_fps(self) -> float:
        return self.target_fps
