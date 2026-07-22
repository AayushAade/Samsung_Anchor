import time
from datetime import datetime
from src.perception.sensor_models import FrameData


class CameraPipeline:
    """
    Modular video frame acquisition and synchronization pipeline.
    """

    def __init__(self, target_fps: float = 30.0) -> None:
        self.target_fps = target_fps
        self._frame_counter = 0
        self._last_time = time.perf_counter()

    def acquire_frame(self) -> FrameData:
        self._frame_counter += 1
        now = time.perf_counter()
        elapsed = now - self._last_time
        self._last_time = now
        fps = round(1.0 / max(elapsed, 0.001), 1)

        return FrameData(
            frame_id=self._frame_counter,
            timestamp=datetime.now().isoformat(),
            width=1280,
            height=720,
            fps=min(fps, self.target_fps),
        )

    def get_fps(self) -> float:
        return self.target_fps
