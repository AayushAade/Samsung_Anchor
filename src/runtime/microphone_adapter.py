from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
from src.runtime.runtime_models import DeviceStatus

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    pyaudio = None
    HAS_PYAUDIO = False


class MicrophoneAdapter(ABC):
    """
    Abstract Microphone Hardware Adapter.
    """

    @abstractmethod
    def initialize(self) -> bool:
        pass

    @abstractmethod
    def read_chunk(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_status(self) -> DeviceStatus:
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass


class SimulatedMicrophoneAdapter(MicrophoneAdapter):
    """
    Simulated Microphone Adapter.
    """

    def __init__(self, device_name: str = "Simulated_Mic_0") -> None:
        self.device_name = device_name
        self.status = DeviceStatus.DISCONNECTED
        self.sample_counter = 0

    def initialize(self) -> bool:
        self.status = DeviceStatus.HEALTHY
        return True

    def read_chunk(self) -> Dict[str, Any]:
        self.sample_counter += 1
        return {
            "chunk_id": self.sample_counter,
            "device": self.device_name,
            "sample_rate": 16000,
            "channels": 1,
            "latency_ms": 12.5,
            "timestamp": datetime.now().isoformat(),
            "raw_audio": None,
        }

    def get_status(self) -> DeviceStatus:
        return self.status

    def shutdown(self) -> None:
        self.status = DeviceStatus.DISCONNECTED


class PyAudioMicrophoneAdapter(MicrophoneAdapter):
    """
    Production-grade PyAudio Microphone Adapter capturing real physical audio streams.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        channels: int = 1,
        device_index: Optional[int] = None,
        device_name: str = "PyAudio_Microphone_0",
    ) -> None:
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.device_index = device_index
        self.device_name = device_name
        self.status = DeviceStatus.DISCONNECTED
        self.p: Optional[Any] = None
        self.stream: Optional[Any] = None
        self.sample_counter = 0

    def initialize(self) -> bool:
        if not HAS_PYAUDIO:
            self.status = DeviceStatus.FAULTED
            return False

        try:
            self.p = pyaudio.PyAudio()

            # Hardware input device index resolution
            target_idx = self.device_index
            if target_idx is None:
                # 1. Check if device_name matches an available hardware device
                if self.device_name and self.device_name not in ["Default_Mic", "PyAudio_Microphone_0"]:
                    for i in range(self.p.get_device_count()):
                        info = self.p.get_device_info_by_index(i)
                        if info.get("maxInputChannels", 0) > 0 and self.device_name.lower() in info.get("name", "").lower():
                            target_idx = i
                            break

                # 2. If target_idx is still None, inspect system default input device
                if target_idx is None:
                    try:
                        default_info = self.p.get_default_input_device_info()
                        def_idx = default_info.get("index", 0)
                        def_name = default_info.get("name", "")
                        target_idx = def_idx

                        # Fallback override if default device is an idle/muted Bluetooth headset
                        if any(b_name in def_name.lower() for b_name in ["buds", "airpods", "headset", "bluetooth"]):
                            for i in range(self.p.get_device_count()):
                                info = self.p.get_device_info_by_index(i)
                                if info.get("maxInputChannels", 0) > 0 and any(m_name in info.get("name", "").lower() for m_name in ["built-in", "macbook", "microphone"]):
                                    target_idx = i
                                    break
                    except Exception:
                        target_idx = None

            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=target_idx,
                frames_per_buffer=self.chunk_size,
            )
            if self.stream and self.stream.is_active():
                self.status = DeviceStatus.HEALTHY
                return True
            else:
                self.status = DeviceStatus.FAULTED
                return False
        except Exception:
            self.status = DeviceStatus.FAULTED
            return False

    def read_chunk(self) -> Dict[str, Any]:
        self.sample_counter += 1
        now_iso = datetime.now().isoformat()

        if self.status == DeviceStatus.HEALTHY and self.stream and self.stream.is_active():
            try:
                raw_audio = self.stream.read(self.chunk_size, exception_on_overflow=False)
                return {
                    "chunk_id": self.sample_counter,
                    "device": self.device_name,
                    "sample_rate": self.sample_rate,
                    "channels": self.channels,
                    "dtype": "int16",
                    "latency_ms": 12.5,
                    "timestamp": now_iso,
                    "raw_audio": raw_audio,
                }
            except Exception:
                pass

        # Fallback metadata payload if stream read fails
        return {
            "chunk_id": self.sample_counter,
            "device": self.device_name,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "dtype": "int16",
            "latency_ms": 12.5,
            "timestamp": now_iso,
            "raw_audio": None,
        }

    def get_status(self) -> DeviceStatus:
        return self.status

    def shutdown(self) -> None:
        try:
            if self.stream:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
            if self.p:
                self.p.terminate()
        except Exception:
            pass

        self.stream = None
        self.p = None
        self.status = DeviceStatus.DISCONNECTED
