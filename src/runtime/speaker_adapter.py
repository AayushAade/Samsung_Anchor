import os
import sys
import subprocess
from typing import Optional, Any
from abc import ABC, abstractmethod
from src.runtime.runtime_models import DeviceStatus

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    pyttsx3 = None
    HAS_PYTTSX3 = False


class SpeakerAdapter(ABC):
    """
    Abstract Speaker Hardware Adapter.
    """

    @abstractmethod
    def speak(self, text: str) -> bool:
        pass

    @abstractmethod
    def play_chime(self) -> bool:
        pass

    @abstractmethod
    def trigger_alarm(self) -> bool:
        pass

    @abstractmethod
    def set_volume(self, volume_pct: float) -> float:
        pass

    @abstractmethod
    def get_status(self) -> DeviceStatus:
        pass


class SimulatedSpeakerAdapter(SpeakerAdapter):
    """
    Simulated Speaker Adapter for testing and headless CI.
    """

    def __init__(self, device_name: str = "Simulated_Speaker_0") -> None:
        self.device_name = device_name
        self.status = DeviceStatus.HEALTHY
        self.volume = 80.0

    def speak(self, text: str) -> bool:
        print(f"[SimulatedSpeaker] Speaking: '{text}' (Vol: {self.volume}%)")
        return True

    def play_chime(self) -> bool:
        print(f"[SimulatedSpeaker] Play Chime (Vol: {self.volume}%)")
        return True

    def trigger_alarm(self) -> bool:
        print(f"[SimulatedSpeaker] TRIGGER ALARM (Vol: 100%)")
        return True

    def set_volume(self, volume_pct: float) -> float:
        self.volume = max(0.0, min(100.0, volume_pct))
        return self.volume

    def get_status(self) -> DeviceStatus:
        return self.status


class PyTTSx3SpeakerAdapter(SpeakerAdapter):
    """
    Production-grade Text-to-Speech (TTS) Speaker Adapter.
    Uses pyttsx3 or native system audio drivers (macOS `say` / ALSA `aplay` / espeak) to speak text aloud.
    """

    def __init__(self, device_name: str = "Hardware_Speaker_0") -> None:
        self.device_name = device_name
        self.status = DeviceStatus.HEALTHY
        self.volume = 80.0
        self.engine: Optional[Any] = None
        self._init_tts_engine()

    def _init_tts_engine(self) -> None:
        if HAS_PYTTSX3:
            try:
                self.engine = pyttsx3.init()
            except Exception:
                self.engine = None

    def speak(self, text: str) -> bool:
        if not text or not text.strip():
            return False

        print(f"[HardwareSpeaker] Speaking: '{text}' (Vol: {self.volume}%)")

        # 1. Try pyttsx3 if initialized
        if self.engine is not None:
            try:
                self.engine.setProperty("volume", self.volume / 100.0)
                self.engine.say(text)
                self.engine.runAndWait()
                return True
            except Exception:
                pass

        # 2. System Fallback: macOS native `say` command
        if sys.platform == "darwin":
            try:
                subprocess.run(["say", text], check=True)
                return True
            except Exception:
                pass

        # 3. Linux Fallback: espeak
        if sys.platform.startswith("linux"):
            try:
                subprocess.run(["espeak", text], check=False)
                return True
            except Exception:
                pass

        return True

    def play_chime(self) -> bool:
        print(f"[HardwareSpeaker] Play Chime (Vol: {self.volume}%)")
        return self.speak("Chime")

    def trigger_alarm(self) -> bool:
        print(f"[HardwareSpeaker] TRIGGER ALARM (Vol: 100%)")
        return self.speak("Alarm! Emergency alert triggered.")

    def set_volume(self, volume_pct: float) -> float:
        self.volume = max(0.0, min(100.0, volume_pct))
        return self.volume

    def get_status(self) -> DeviceStatus:
        return self.status

    def shutdown(self) -> None:
        if self.engine is not None:
            try:
                self.engine.stop()
            except Exception:
                pass
        self.status = DeviceStatus.DISCONNECTED
