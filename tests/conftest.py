"""
Shared pytest configuration.

Every test session runs against a throwaway database directory so that the
suite can never read, modify, or delete the operator's real MEMORA data
(memora_db_v2.sqlite and its face-embedding files in the repository root).
"""

from __future__ import annotations

import os
import tempfile

import pytest

_SESSION_DIR = tempfile.mkdtemp(prefix="memora-tests-")
os.environ["MEMORA_DB_PATH"] = os.path.join(_SESSION_DIR, "memora_test_db.sqlite")
os.environ["MEMORA_LOG_DIR"] = os.path.join(_SESSION_DIR, "logs")

from config import settings  # noqa: E402  (must follow the environment override)

settings.DB_PATH = os.environ["MEMORA_DB_PATH"]
settings.LOG_DIR = os.environ["MEMORA_LOG_DIR"]


@pytest.fixture(autouse=True, scope="session")
def _isolated_database_path():
    real_default = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "memora_db_v2.sqlite"))
    assert os.path.abspath(settings.DB_PATH) != real_default
    yield settings.DB_PATH
    # Remove this session's synthetic databases and logs.
    import shutil
    shutil.rmtree(_SESSION_DIR, ignore_errors=True)


# ---------------------------------------------------------------------------
# No physical devices in tests: camera, microphone, and speech output are
# replaced for every test, so the suite can never open the camera, record
# audio, or make sound on the machine running it.
# ---------------------------------------------------------------------------

class _NoCamera:
    def __init__(self, *args, **kwargs):
        pass

    def isOpened(self):
        return False

    def read(self):
        return False, None

    def set(self, *args):
        return False

    def get(self, *args):
        return 0.0

    def release(self):
        pass


class _NoAudio:
    def __init__(self, *args, **kwargs):
        raise OSError("Audio devices are disabled in the test suite")


class _SilentEngine:
    def __init__(self):
        self.said = []

    def setProperty(self, *args):
        pass

    def getProperty(self, *args):
        return []

    def say(self, text):
        self.said.append(text)

    def runAndWait(self):
        pass

    def stop(self):
        pass


_AUDIO_COMMANDS = {"say", "espeak", "aplay", "afplay", "paplay"}


@pytest.fixture(autouse=True)
def _no_physical_devices(monkeypatch):
    import subprocess

    try:
        import cv2
        monkeypatch.setattr(cv2, "VideoCapture", _NoCamera)
    except ImportError:
        pass
    try:
        import pyaudio
        monkeypatch.setattr(pyaudio, "PyAudio", _NoAudio)
    except ImportError:
        pass
    try:
        import pyttsx3
        monkeypatch.setattr(pyttsx3, "init", lambda *a, **k: _SilentEngine())
    except ImportError:
        pass

    real_run, real_popen = subprocess.run, subprocess.Popen

    def _is_audio(cmd):
        return isinstance(cmd, (list, tuple)) and cmd and str(cmd[0]).split("/")[-1] in _AUDIO_COMMANDS

    def guarded_run(cmd, *args, **kwargs):
        if _is_audio(cmd):
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return real_run(cmd, *args, **kwargs)

    class _NoProcess:
        def __init__(self, cmd):
            self.args, self.returncode = cmd, 0

        def wait(self, *a, **k):
            return 0

        def communicate(self, *a, **k):
            return "", ""

    def guarded_popen(cmd, *args, **kwargs):
        if _is_audio(cmd):
            return _NoProcess(cmd)
        return real_popen(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", guarded_run)
    monkeypatch.setattr(subprocess, "Popen", guarded_popen)
    yield
