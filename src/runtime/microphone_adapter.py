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
    Scans PyAudio input devices, reports explicit technical failure diagnostics.
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
        self.failure_reason: Optional[str] = None
        self.actual_device_name: str = "NONE"
        self.actual_device_index: int = -1
        self.audio_energy_rms: float = 0.0

    @classmethod
    def enumerate_microphones(cls) -> list[dict[str, Any]]:
        """Scans PyAudio input devices and returns detailed metadata list."""
        available = []
        if not HAS_PYAUDIO:
            return available

        try:
            p = pyaudio.PyAudio()
            def_idx = -1
            try:
                def_info = p.get_default_input_device_info()
                def_idx = def_info.get("index", -1)
            except Exception:
                pass

            for i in range(p.get_device_count()):
                try:
                    info = p.get_device_info_by_index(i)
                    max_in = info.get("maxInputChannels", 0)
                    if max_in > 0:
                        available.append({
                            "index": i,
                            "name": info.get("name", "Unknown"),
                            "channels": max_in,
                            "sample_rate": int(info.get("defaultSampleRate", 16000)),
                            "is_default": (i == def_idx),
                        })
                except Exception:
                    pass
            p.terminate()
        except Exception:
            pass

        return available

    def initialize(self) -> bool:
        if not HAS_PYAUDIO:
            self.status = DeviceStatus.FAULTED
            self.failure_reason = "PyAudio Python library is not installed."
            return False

        try:
            self.p = pyaudio.PyAudio()
            device_cnt = self.p.get_device_count()

            if device_cnt == 0:
                self.status = DeviceStatus.FAULTED
                self.failure_reason = "PortAudio reports 0 accessible input microphone devices."
                return False

            target_idx = self.device_index
            if target_idx is None:
                # 1. Check if device_name matches an available hardware device
                if self.device_name and self.device_name not in ["Default_Mic", "PyAudio_Microphone_0"]:
                    for i in range(device_cnt):
                        info = self.p.get_device_info_by_index(i)
                        if info.get("maxInputChannels", 0) > 0 and self.device_name.lower() in info.get("name", "").lower():
                            target_idx = i
                            break

                # 2. If target_idx is still None, inspect system default input device
                if target_idx is None:
                    try:
                        default_info = self.p.get_default_input_device_info()
                        target_idx = default_info.get("index", 0)
                    except Exception:
                        target_idx = 0

            if target_idx is None or target_idx < 0 or target_idx >= device_cnt:
                self.status = DeviceStatus.FAULTED
                self.failure_reason = f"Microphone device index {target_idx} is out of bounds [0..{device_cnt-1}]."
                return False

            dev_info = self.p.get_device_info_by_index(target_idx)
            if dev_info.get("maxInputChannels", 0) <= 0:
                self.status = DeviceStatus.FAULTED
                self.failure_reason = f"Microphone device index {target_idx} ({dev_info.get('name')}) has 0 input channels."
                return False

            self.actual_device_index = target_idx
            self.actual_device_name = dev_info.get("name", f"Microphone_{target_idx}")

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
                self.failure_reason = None
                return True
            else:
                self.status = DeviceStatus.FAULTED
                self.failure_reason = f"PortAudio stream failed to activate on device {target_idx} ({self.actual_device_name})."
                return False
        except Exception as e:
            self.status = DeviceStatus.FAULTED
            self.failure_reason = f"PortAudio error initializing microphone device: {e}"
            return False

    def read_chunk(self) -> Dict[str, Any]:
        self.sample_counter += 1
        now_iso = datetime.now().isoformat()

        if self.status == DeviceStatus.HEALTHY and self.stream and self.stream.is_active():
            try:
                raw_audio = self.stream.read(self.chunk_size, exception_on_overflow=False)
                # Compute RMS energy for diagnostic monitoring
                import struct, math
                shorts = struct.unpack(f"{len(raw_audio)//2}h", raw_audio) if len(raw_audio) >= 2 else []
                sum_sq = sum(s * s for s in shorts)
                self.audio_energy_rms = math.sqrt(sum_sq / len(shorts)) if shorts else 0.0

                return {
                    "chunk_id": self.sample_counter,
                    "device": self.actual_device_name,
                    "sample_rate": self.sample_rate,
                    "channels": self.channels,
                    "dtype": "int16",
                    "latency_ms": 12.5,
                    "timestamp": now_iso,
                    "raw_audio": raw_audio,
                    "energy_rms": self.audio_energy_rms,
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
            "energy_rms": 0.0,
        }

    def get_status(self) -> DeviceStatus:
        return self.status

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "device_index": self.actual_device_index,
            "device_name": self.actual_device_name,
            "format": f"{self.sample_rate}Hz, {self.channels}ch (int16)",
            "chunks_processed": self.sample_counter,
            "audio_energy_rms": round(self.audio_energy_rms, 2),
            "failure_reason": self.failure_reason,
        }

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
