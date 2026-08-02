import os
import sys
import subprocess
from typing import Optional, Any, Dict
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
        self.status = DeviceStatus.DISCONNECTED
        self.volume = 80.0
        self.engine: Optional[Any] = None
        self.voice_engine_name: str = "NONE"
        self.failure_reason: Optional[str] = None
        self.spoken_count = 0
        self.initialize()

    def initialize(self) -> bool:
        self._init_tts_engine()

        if self.engine is not None:
            self.voice_engine_name = "pyttsx3 (Native Speech Synthesizer)"
            self.status = DeviceStatus.HEALTHY
            self.failure_reason = None
            return True

        if sys.platform == "darwin":
            # Test if system say command exists
            try:
                res = subprocess.run(["which", "say"], capture_output=True, text=True)
                if res.returncode == 0:
                    self.voice_engine_name = "macOS say CLI"
                    self.status = DeviceStatus.HEALTHY
                    self.failure_reason = None
                    return True
            except Exception:
                pass

        if sys.platform.startswith("linux"):
            try:
                res = subprocess.run(["which", "espeak"], capture_output=True, text=True)
                if res.returncode == 0:
                    self.voice_engine_name = "Linux espeak CLI"
                    self.status = DeviceStatus.HEALTHY
                    self.failure_reason = None
                    return True
            except Exception:
                pass

        self.status = DeviceStatus.FAULTED
        self.voice_engine_name = "Console Fallback"
        self.failure_reason = "pyttsx3 engine, macOS 'say', and Linux 'espeak' system commands are unavailable."
        return False

    def _init_tts_engine(self) -> None:
        if HAS_PYTTSX3:
            try:
                self.engine = pyttsx3.init()
            except Exception as e:
                self.engine = None
                self.failure_reason = f"pyttsx3.init() exception: {e}"

    def speak(self, text: str) -> bool:
        if not text or not text.strip():
            return False

        self.spoken_count += 1
        print(f"[HardwareSpeaker] Speaking: '{text}' (Vol: {self.volume}%)")

        # 1. Try pyttsx3 if initialized
        if self.engine is not None:
            try:
                self.engine.setProperty("volume", self.volume / 100.0)
                self.engine.say(text)
                self.engine.runAndWait()
                return True
            except Exception as e:
                self.failure_reason = f"pyttsx3 speak error: {e}"

        # 2. System Fallback: macOS native `say` command
        if sys.platform == "darwin":
            try:
                subprocess.run(["say", text], check=True)
                return True
            except Exception as e:
                self.failure_reason = f"macOS say CLI error: {e}"

        # 3. Linux Fallback: espeak
        if sys.platform.startswith("linux"):
            try:
                subprocess.run(["espeak", text], check=False)
                return True
            except Exception as e:
                self.failure_reason = f"Linux espeak CLI error: {e}"

        print(f"[ConsoleSpeaker Fallback] Speaking: '{text}'")
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

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "voice_engine": self.voice_engine_name,
            "volume_pct": self.volume,
            "spoken_count": self.spoken_count,
            "failure_reason": self.failure_reason,
        }

    def shutdown(self) -> None:
        if self.engine is not None:
            try:
                self.engine.stop()
            except Exception:
                pass
        self.status = DeviceStatus.DISCONNECTED
