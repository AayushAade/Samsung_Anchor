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

    def read(self) -> tuple[bool, Any]:
        """
        Duck-typing interface matching OpenCV VideoCapture / CameraDevice.
        Returns (success, raw_frame_or_metadata).
        """
        frame_data = self.capture_frame()
        raw = frame_data.get("raw_frame")
        return True, raw if raw is not None else frame_data


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

    def read(self) -> tuple[bool, Any]:
        return True, self.capture_frame()

    def get_status(self) -> DeviceStatus:
        return self.status

    def shutdown(self) -> None:
        self.status = DeviceStatus.DISCONNECTED


class OpenCVCameraAdapter(CameraAdapter):
    """
    Production-grade OpenCV Camera Adapter capturing physical webcam frames.
    Probes multiple camera backends and indices, reporting explicit failure diagnostics.
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
        self.dropped_frames = 0
        self.failure_reason: Optional[str] = None
        self.selected_backend: str = "NONE"
        self.actual_width: int = 0
        self.actual_height: int = 0
        self.actual_fps: float = 0.0

    @classmethod
    def enumerate_cameras(cls) -> list[dict[str, Any]]:
        """Scans camera indices 0..3 to report accessible hardware cameras."""
        available = []
        if not HAS_OPENCV:
            return available

        import sys
        backends = [cv2.CAP_ANY]
        if sys.platform == "darwin":
            backends = [cv2.CAP_AVFOUNDATION, cv2.CAP_ANY]
        elif sys.platform == "win32":
            backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]
        elif sys.platform.startswith("linux"):
            backends = [cv2.CAP_V4L2, cv2.CAP_ANY]

        for idx in range(4):
            for b in backends:
                try:
                    c = cv2.VideoCapture(idx, b)
                    if c and c.isOpened():
                        ret, f = c.read()
                        if ret and f is not None:
                            h, w = f.shape[:2]
                            b_name = "AVFOUNDATION" if b == getattr(cv2, "CAP_AVFOUNDATION", -1) else ("DSHOW" if b == getattr(cv2, "CAP_DSHOW", -1) else ("V4L2" if b == getattr(cv2, "CAP_V4L2", -1) else "ANY"))
                            available.append({
                                "index": idx,
                                "backend": b_name,
                                "width": w,
                                "height": h,
                                "fps": c.get(cv2.CAP_PROP_FPS) or 30.0,
                            })
                            c.release()
                            break
                        c.release()
                except Exception:
                    pass
        return available

    def initialize(self) -> bool:
        if not HAS_OPENCV:
            self.status = DeviceStatus.FAULTED
            self.failure_reason = "OpenCV (cv2) Python module is not installed."
            return False

        import sys
        backends = []
        if sys.platform == "darwin":
            backends.append(("AVFOUNDATION", cv2.CAP_AVFOUNDATION))
        elif sys.platform == "win32":
            backends.append(("DSHOW", cv2.CAP_DSHOW))
        elif sys.platform.startswith("linux"):
            backends.append(("V4L2", cv2.CAP_V4L2))
        backends.append(("ANY", cv2.CAP_ANY))

        candidate_indices = [self.device_index] if self.device_index != 0 else [0, 1, 2, 3]

        attempt_log = []
        for idx in candidate_indices:
            for b_name, b_flag in backends:
                try:
                    attempt_log.append(f"Index {idx} ({b_name})")
                    c = cv2.VideoCapture(idx, b_flag)
                    if c and c.isOpened():
                        c.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
                        c.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
                        c.set(cv2.CAP_PROP_FPS, self.target_fps)

                        # Test read to verify frame pixels exist
                        ret, test_frame = c.read()
                        if ret and test_frame is not None and test_frame.size > 0:
                            self.cap = c
                            self.device_index = idx
                            self.selected_backend = b_name
                            self.actual_height, self.actual_width = test_frame.shape[:2]
                            self.actual_fps = c.get(cv2.CAP_PROP_FPS) or self.target_fps
                            self.status = DeviceStatus.HEALTHY
                            self.failure_reason = None
                            return True
                        c.release()
                except Exception as e:
                    attempt_log.append(f"Index {idx} ({b_name}) error: {e}")

        self.status = DeviceStatus.FAULTED
        self.failure_reason = f"No accessible camera device found across attempted backends ({', '.join(attempt_log)}). OpenCV isOpened()=False or permission denied."
        return False

    def capture_frame(self) -> Dict[str, Any]:
        self.frame_count += 1
        now_iso = datetime.now().isoformat()

        if self.status == DeviceStatus.HEALTHY and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    h, w = frame.shape[:2]
                    self.actual_width, self.actual_height = w, h
                    return {
                        "frame_id": self.frame_count,
                        "device": self.device_name,
                        "width": w,
                        "height": h,
                        "fps": self.actual_fps,
                        "timestamp": now_iso,
                        "raw_frame": frame,
                    }
                else:
                    self.dropped_frames += 1
            except Exception:
                self.dropped_frames += 1

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

    def read(self) -> tuple[bool, Any]:
        frame_data = self.capture_frame()
        raw = frame_data.get("raw_frame")
        return (raw is not None if self.status == DeviceStatus.HEALTHY else True), (raw if raw is not None else frame_data)

    def get_status(self) -> DeviceStatus:
        return self.status

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "backend": self.selected_backend,
            "device_index": self.device_index,
            "device_name": self.device_name,
            "resolution": f"{self.actual_width or self.target_width}x{self.actual_height or self.target_height}",
            "fps": self.actual_fps or self.target_fps,
            "processed_frames": self.frame_count,
            "dropped_frames": self.dropped_frames,
            "failure_reason": self.failure_reason,
        }

    def shutdown(self) -> None:
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.cap = None
        self.status = DeviceStatus.DISCONNECTED
