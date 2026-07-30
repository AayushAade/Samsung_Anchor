"""
Unit and Integration Tests for Operations Control Plane (Phase 20).
"""

import os
import pytest
from src.operations.orchestrator import SystemOrchestrator
from src.operations.operational_event_bus import OperationalEventBus, OperationalEventType
from src.operations.session_recorder import SessionRecorder
from src.operations.startup_validator import StartupValidator


def test_system_orchestrator_registry():
    """Verify SystemOrchestrator registers subsystems and tracks health summary."""
    orchestrator = SystemOrchestrator()
    summary = orchestrator.get_system_health_summary()
    assert summary["overall_status"] in ("HEALTHY", "WARNING", "FAILED")
    assert summary["total_subsystems"] >= 10
    assert "Vision Pipeline" in summary["subsystems"]


def test_operational_event_bus():
    """Verify OperationalEventBus publishes and receives events."""
    bus = OperationalEventBus()
    received_events = []

    def callback(event):
        received_events.append(event)

    bus.subscribe(callback)
    bus.publish(OperationalEventType.RECOGNITION_COMPLETED, "Face Recognizer", {"name": "Eleanor"})

    assert len(received_events) >= 1
    latest = received_events[-1]
    assert latest.event_type == OperationalEventType.RECOGNITION_COMPLETED
    assert latest.subsystem == "Face Recognizer"
    assert latest.payload["name"] == "Eleanor"


def test_session_recorder_export():
    """Verify SessionRecorder captures events and exports JSON/MD artifacts."""
    recorder = SessionRecorder(session_name="Test_Session")
    recorder.record_event("Test", "Init Test Event", {"status": "OK"})
    json_path, md_path = recorder.export_session(output_dir="validation/artifacts")

    assert os.path.exists(json_path)
    assert os.path.exists(md_path)


def test_startup_validator():
    """Verify StartupValidator executes pre-demo health checks."""
    validator = StartupValidator()
    results = validator.run_all_checks()
    assert len(results) >= 5
    statuses = [r.status for r in results]
    assert "FAIL" not in statuses
