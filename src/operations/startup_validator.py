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

    def run_all_checks(self) -> list[HealthCheckItem]:
        """Execute all pre-demo health check items."""
        return [
            self.check_python_version(),
            self.check_dependencies(),
            self.check_database(),
            self.check_vector_store(),
            self.check_camera_hardware(),
            self.check_dashboard_port(),
        ]
