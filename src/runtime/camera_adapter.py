from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
from src.runtime.runtime_models import DeviceStatus

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    cv2 = None
    HAS_OPENCV = False


class CameraAdapter(ABC):
    """
    Abstract Camera Hardware Adapter.
    """

    @abstractmethod
    def initialize(self) -> bool:
        pass

    @abstractmethod
    def capture_frame(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_status(self) -> DeviceStatus:
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass


class SimulatedCameraAdapter(CameraAdapter):
    """
    Simulated Camera Adapter for software verification and desktop testing.
    """

    def __init__(self, device_name: str = "Simulated_Camera_0") -> None:
        self.device_name = device_name
        self.status = DeviceStatus.DISCONNECTED
        self.frame_count = 0

    def initialize(self) -> bool:
        self.status = DeviceStatus.HEALTHY
        return True

    def capture_frame(self) -> Dict[str, Any]:
        self.frame_count += 1
        return {
            "frame_id": self.frame_count,
            "device": self.device_name,
            "width": 1280,
            "height": 720,
            "fps": 30.0,
            "timestamp": datetime.now().isoformat(),
        }

    def get_status(self) -> DeviceStatus:
        return self.status

    def shutdown(self) -> None:
        self.status = DeviceStatus.DISCONNECTED


class OpenCVCameraAdapter(CameraAdapter):
    """
    Production-grade OpenCV Camera Adapter capturing physical webcam frames.
    """

    def __init__(
        self,
        device_index: int = 0,
        target_width: int = 1280,
        target_height: int = 720,
        target_fps: float = 30.0,
        device_name: str = "OpenCV_Webcam_0",
    ) -> None:
        self.device_index = device_index
        self.target_width = target_width
        self.target_height = target_height
        self.target_fps = target_fps
        self.device_name = device_name
        self.status = DeviceStatus.DISCONNECTED
        self.cap: Optional[Any] = None
        self.frame_count = 0

    def initialize(self) -> bool:
        if not HAS_OPENCV:
            self.status = DeviceStatus.FAULTED
            return False

        try:
            self.cap = cv2.VideoCapture(self.device_index)
            if self.cap and self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
                self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
                self.status = DeviceStatus.HEALTHY
                return True
            else:
                self.status = DeviceStatus.FAULTED
                return False
        except Exception:
            self.status = DeviceStatus.FAULTED
            return False

    def capture_frame(self) -> Dict[str, Any]:
        self.frame_count += 1
        now_iso = datetime.now().isoformat()

        if self.status == DeviceStatus.HEALTHY and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                return {
                    "frame_id": self.frame_count,
                    "device": self.device_name,
                    "width": w,
                    "height": h,
                    "fps": self.target_fps,
                    "timestamp": now_iso,
                    "raw_frame": frame,
                }

        # Fallback metadata generation if capture fails
        return {
            "frame_id": self.frame_count,
            "device": self.device_name,
            "width": self.target_width,
            "height": self.target_height,
            "fps": self.target_fps,
            "timestamp": now_iso,
            "raw_frame": None,
        }

    def get_status(self) -> DeviceStatus:
        return self.status

    def shutdown(self) -> None:
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.cap = None
        self.status = DeviceStatus.DISCONNECTED
