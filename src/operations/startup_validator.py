"""
MEMORA Pre-Demo Health Check & Pre-Flight Startup Validator.

Verifies hardware, database, dependencies, directories, vector store,
and port availability before runtime initialization.
"""

from __future__ import annotations

import os
import socket
import sys
from dataclasses import dataclass
from typing import Any


@dataclass
class HealthCheckItem:
    component: str
    status: str                         # PASS, WARNING, FAIL
    message: str
    remediation: str = "None required"

    def to_dict(self) -> dict[str, Any]:
        return {
            "component": self.component,
            "status": self.status,
            "message": self.message,
            "remediation": self.remediation,
        }


class StartupValidator:
    """
    Executes pre-demo health checks and pre-flight startup validation.
    """

    def __init__(self) -> None:
        self.results: list[HealthCheckItem] = []

    def check_python_version(self) -> HealthCheckItem:
        """Verify Python version is >= 3.10."""
        major, minor = sys.version_info[:2]
        if major >= 3 and minor >= 10:
            return HealthCheckItem(
                component="Python Environment",
                status="PASS",
                message=f"Python {major}.{minor} meets minimum requirements",
            )
        return HealthCheckItem(
            component="Python Environment",
            status="FAIL",
            message=f"Python {major}.{minor} is below minimum 3.10 requirement",
            remediation="Upgrade to Python 3.11 in virtual environment",
        )

    def check_dependencies(self) -> HealthCheckItem:
        """Verify critical Python package dependencies."""
        missing = []
        for pkg in ["sqlalchemy", "numpy", "faiss"]:
            try:
                __import__(pkg)
            except ImportError:
                missing.append(pkg)

        if not missing:
            return HealthCheckItem(
                component="Software Dependencies",
                status="PASS",
                message="All core packages (SQLAlchemy, NumPy, FAISS) imported successfully",
            )
        return HealthCheckItem(
            component="Software Dependencies",
            status="FAIL",
            message=f"Missing required packages: {', '.join(missing)}",
            remediation="Run `pip install -r requirements.txt`",
        )

    def check_database(self) -> HealthCheckItem:
        """Verify SQLite memory database initialization."""
        try:
            from src.memory.database import MemoraDatabase
            with MemoraDatabase("sqlite:///:memory:") as db:
                db.set_current_room("Living Room")
                assert db.get_current_room() == "Living Room"
            return HealthCheckItem(
                component="SQLite Database & ORM",
                status="PASS",
                message="In-memory SQLite database initialized and passed read/write check",
            )
        except Exception as e:
            return HealthCheckItem(
                component="SQLite Database & ORM",
                status="FAIL",
                message=f"Database initialization failed: {e}",
                remediation="Verify SQLAlchemy and SQLite file permissions",
            )

    def check_vector_store(self) -> HealthCheckItem:
        """Verify FAISS vector store initialization."""
        try:
            from src.memory.vector_store import FaissVectorStore
            import numpy as np
            # In-memory store only: a health check must never write to user data.
            vs = FaissVectorStore()
            vs.add_embedding("Test_ID", np.zeros(128, dtype=np.float32))
            return HealthCheckItem(
                component="FAISS Vector Store",
                status="PASS",
                message="FAISS 128D vector index initialized and passed embedding insertion check",
            )
        except Exception as e:
            return HealthCheckItem(
                component="FAISS Vector Store",
                status="FAIL",
                message=f"FAISS index error: {e}",
                remediation="Verify OpenMP environment variables and FAISS installation",
            )

    def check_camera_hardware(self) -> HealthCheckItem:
        """Verify Camera HAL hardware or fallback status."""
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if cap and cap.isOpened():
                cap.release()
                return HealthCheckItem(
                    component="Camera HAL Device 0",
                    status="PASS",
                    message="OpenCV physical webcam hardware opened successfully",
                )
            return HealthCheckItem(
                component="Camera HAL Device 0",
                status="WARNING",
                message="Physical webcam unavailable; fallback SimulatedCameraAdapter active",
                remediation="Connect USB webcam or run in --simulation mode",
            )
        except Exception:
            return HealthCheckItem(
                component="Camera HAL Device 0",
                status="WARNING",
                message="OpenCV hardware check failed; fallback SimulatedCameraAdapter active",
                remediation="Connect USB webcam or run in --simulation mode",
            )

    def check_dashboard_port(self) -> HealthCheckItem:
        """Verify dashboard WebSocket port 8765 availability."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex(("127.0.0.1", 8765))
        sock.close()

        if result != 0:
            return HealthCheckItem(
                component="Dashboard Port 8765",
                status="PASS",
                message="Port 8765 is open and ready for WebSockets Experience Server",
            )
        return HealthCheckItem(
            component="Dashboard Port 8765",
            status="WARNING",
            message="Port 8765 is currently in use by an active dashboard server",
            remediation="Kill existing server process or connect to active dashboard",
        )

    def check_user_database(self) -> HealthCheckItem:
        """
        Check the configured user database and cross-check identities against face embeddings.

        Read-only by construction: the check runs on a temporary copy of the database and
        its face files, so a diagnostic never migrates, re-permissions or creates the
        person's real database.
        """
        import shutil
        import tempfile
        from config import settings
        from src.memory.database import MemoraDatabase, resolve_db_url, vector_store_paths
        actual = resolve_db_url(settings.DB_PATH)[1] or settings.DB_PATH
        if actual and not os.path.exists(actual):
            return HealthCheckItem(component="User Memory Database", status="PASS",
                                   message=f"{actual}: no database yet; it will be created on first use")
        scratch = tempfile.mkdtemp(prefix="memora-check-")
        try:
            copy = os.path.join(scratch, os.path.basename(actual))
            shutil.copy2(actual, copy)
            for live, dup in zip(vector_store_paths(actual), vector_store_paths(copy)):
                if os.path.exists(live):
                    shutil.copy2(live, dup)
            with MemoraDatabase(copy) as db:
                report = db.check_integrity()
            path = actual
        except Exception as e:
            return HealthCheckItem(component="User Memory Database", status="FAIL",
                                   message=f"Cannot open {actual}: {e}",
                                   remediation="Check the path (MEMORA_DB_PATH) and file permissions; "
                                               "restore from backup if the file is corrupt")
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        if report["ok"]:
            return HealthCheckItem(component="User Memory Database", status="PASS",
                                   message=f"{path}: {report['identities']} people, consistent")
        problems = []
        if report["identities_without_embeddings"]:
            problems.append(f"{len(report['identities_without_embeddings'])} people have no face data")
        if report["orphan_embedding_identities"]:
            problems.append("face data for unknown people")
        problems += [report[k] for k in ("vector_store_load_error", "vector_store_save_error") if report[k]]
        return HealthCheckItem(component="User Memory Database", status="WARNING",
                               message=f"{path}: " + "; ".join(problems),
                               remediation="Run `python inspect_database.py` for details; re-enrol affected people")

    def check_optional_capabilities(self) -> HealthCheckItem:
        """Report which optional sensor/model/cloud packages are installed (not whether they work)."""
        import importlib.util
        optional = {"faster_whisper": "speech-to-text", "speech_recognition": "microphone capture",
                    "pyaudio": "microphone", "pyttsx3": "voice output",
                    "insightface": "face recognition", "mediapipe": "face landmarks", "google.genai": "Gemini"}
        missing = []
        for mod, label in optional.items():
            try:
                found = importlib.util.find_spec(mod) is not None
            except (ImportError, ValueError):
                found = False
            if not found:
                missing.append(label)
        if not missing:
            return HealthCheckItem(component="Optional Capabilities", status="PASS",
                                   message="All optional packages installed (functionality not tested here)")
        return HealthCheckItem(component="Optional Capabilities", status="WARNING",
                               message="Not installed: " + ", ".join(missing),
                               remediation="pip install -r requirements-hardware.txt / requirements-cloud.txt if needed")

    def check_network_use(self) -> HealthCheckItem:
        """Report which features could send data off this computer (none by default)."""
        from src.network_policy import describe, cloud_asr_allowed, cloud_llm_allowed
        lines = describe()
        sends_data = cloud_asr_allowed() or cloud_llm_allowed()
        return HealthCheckItem(component="Network Use", status="WARNING" if sends_data else "PASS",
                               message=" ".join(lines),
                               remediation="Unset MEMORA_ALLOW_* variables to keep everything on this computer"
                               if sends_data else None)

    def check_media_library_conflict(self, platform: str | None = None) -> HealthCheckItem:
        """
        macOS: PyAV (needed by faster-whisper) and OpenCV each bundle FFmpeg's libavdevice.
        Loading both in one process makes the Objective-C runtime warn of duplicate classes
        (upstream PyAV issue #2215). Inspected on disk, without importing either package.
        """
        import glob
        import importlib.util
        import sys
        platform = platform or sys.platform
        found = {}
        for pkg in ("av", "cv2"):
            spec = importlib.util.find_spec(pkg)
            if spec and spec.submodule_search_locations:
                root = list(spec.submodule_search_locations)[0]
                found[pkg] = sorted(os.path.basename(p) for p in glob.glob(os.path.join(root, ".dylibs", "libavdevice*")))
        if platform != "darwin" or not (found.get("av") and found.get("cv2")):
            return HealthCheckItem(component="Media Libraries", status="PASS",
                                   message="No duplicate FFmpeg device library")
        return HealthCheckItem(
            component="Media Libraries", status="WARNING",
            message=(f"PyAV ({', '.join(found['av'])}) and OpenCV ({', '.join(found['cv2'])}) both bundle "
                     "libavdevice. Text chat is unaffected; voice mode loads both (not yet hardware-tested)"),
            remediation="Before relying on voice mode, follow docs/HARDWARE_TEST_CHECKLIST.md section R-09")

    def run_all_checks(self, include_camera: bool = True) -> list[HealthCheckItem]:
        """
        Execute all health check items. include_camera=False avoids opening the
        physical camera (which activates it and may prompt for permission).
        """
        checks = [
            self.check_python_version(),
            self.check_dependencies(),
            self.check_database(),
            self.check_vector_store(),
            self.check_user_database(),
            self.check_optional_capabilities(),
            self.check_network_use(),
            self.check_media_library_conflict(),
        ]
        if include_camera:
            checks.append(self.check_camera_hardware())
        checks.append(self.check_dashboard_port())
        return checks
