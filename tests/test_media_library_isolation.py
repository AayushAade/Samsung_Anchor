"""
macOS risk R-09: PyAV (pulled in by faster-whisper) and OpenCV both bundle FFmpeg's
libavdevice, and loading both in one process triggers an Objective-C duplicate-class
warning (upstream PyAV issue #2215, closed "not planned"). Text chat, simulation and
diagnostics must never load PyAV, so they cannot hit the conflict.
"""

from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROBE = r"""
import contextlib, io, os, sys
with contextlib.redirect_stdout(io.StringIO()):
    from src.application.factory import build_application
    from src.application.chat import ChatSession
    from src.memory.database import MemoraDatabase
    from src.perception.speech_recognition_engine import SpeechRecognitionEngine
    from src.operations.startup_validator import StartupValidator
    coord = build_application(live_hardware=False, database=MemoraDatabase(os.environ["MEMORA_DB_PATH"]))
    session = ChatSession(coord)
    session.opening(); session.handle("yes"); session.handle("I like jasmine tea"); session.close()
    SpeechRecognitionEngine()
    StartupValidator().run_all_checks(include_camera=False)
print(sorted(m for m in ("av", "faster_whisper") if m in sys.modules))
"""


def test_text_mode_and_diagnostics_never_import_pyav(tmp_path):
    env = dict(os.environ, MEMORA_DB_PATH=str(tmp_path / "m.sqlite"), MEMORA_LOG_DIR=str(tmp_path / "logs"))
    proc = subprocess.run([sys.executable, "-c", PROBE], cwd=ROOT, env=env, capture_output=True, text=True,
                          timeout=120)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip().splitlines()[-1] == "[]"
    assert "is implemented in both" not in proc.stderr


def test_media_library_check_reports_duplicate_only_on_macos(monkeypatch, tmp_path):
    import importlib.util
    from src.operations import startup_validator as sv

    roots = {}
    for pkg, lib in (("av", "libavdevice.62.3.102.dylib"), ("cv2", "libavdevice.61.3.100.dylib")):
        (tmp_path / pkg / ".dylibs").mkdir(parents=True)
        (tmp_path / pkg / ".dylibs" / lib).write_bytes(b"")
        roots[pkg] = importlib.util.spec_from_loader(pkg, loader=None, is_package=True)
        roots[pkg].submodule_search_locations = [str(tmp_path / pkg)]
    monkeypatch.setattr(importlib.util, "find_spec", lambda name, *a: roots.get(name))
    v = sv.StartupValidator()
    mac = v.check_media_library_conflict(platform="darwin")
    assert mac.status == "WARNING" and "libavdevice.62.3.102" in mac.message and "Text chat is unaffected" in mac.message
    assert v.check_media_library_conflict(platform="linux").status == "PASS"
    roots.pop("av")
    assert v.check_media_library_conflict(platform="darwin").status == "PASS"
