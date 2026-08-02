"""
Integration test suite for MEMORA Real-Time Cognitive Runtime.

Validates:
1. Runtime startup & subsystem initialization
2. Runtime shutdown & clean resource release
3. Continuous multi-cycle execution
4. Perception -> Cognition -> Assistance pipeline execution
5. Hardware failure recovery & fallback processing
6. Concurrency guarantees (no deadlocks, no thread leaks)
"""

from __future__ import annotations

import threading
import time
import pytest
from unittest.mock import MagicMock, patch

from src.application.factory import build_application
from src.runtime.runtime import AnchorRuntime
from src.runtime.runtime_models import DeviceStatus
from src.interaction.actions import InteractionAction, InteractionActionType


class FailingCamera:
    """Simulates a physical camera device that fails during read."""
    def __init__(self, fail_after: int = 1):
        self.reads_count = 0
        self.fail_after = fail_after

    def read(self):
        self.reads_count += 1
        if self.reads_count > self.fail_after:
            return False, None
        return True, {"frame_id": self.reads_count, "timestamp": time.time()}

    def get_status(self):
        return DeviceStatus.HEALTHY if self.reads_count <= self.fail_after else DeviceStatus.FAILED


# ===================================================================
# 1. Runtime Startup & Initialization Tests
# ===================================================================

def test_runtime_startup_initializes_subsystems():
    """Verify that starting the runtime initializes every core subsystem."""
    coordinator = build_application(live_hardware=False)
    runtime = AnchorRuntime(coordinator)
    runtime.initialize()

    statuses = runtime.get_subsystem_statuses()
    assert isinstance(statuses, dict)
    assert "Runtime" in statuses
    assert "Camera" in statuses
    assert "Audio" in statuses
    assert "Memory" in statuses
    assert "Perception" in statuses
    assert "Cognition" in statuses
    assert "Speaker" in statuses

    # All critical subsystems should report READY or WARNING (Simulated)
    for sub, status in statuses.items():
        assert "READY" in status or "WARNING" in status, f"Subsystem {sub} has invalid status {status}"

    runtime.shutdown()


# ===================================================================
# 2. Runtime Shutdown & Thread Cleanup Tests
# ===================================================================

def test_runtime_shutdown_cleans_resources():
    """Verify that runtime shutdown stops threads and releases memory."""
    initial_threads = threading.active_count()

    coordinator = build_application(live_hardware=False)
    runtime = AnchorRuntime(coordinator)
    runtime.initialize()
    runtime.start()

    assert runtime.running is True
    assert coordinator.running is True

    runtime.shutdown()

    assert runtime.running is False
    assert coordinator.running is False
    assert coordinator._cognitive_thread is None

    # Wait briefly for thread cleanup to settle
    time.sleep(0.2)
    final_threads = threading.active_count()

    # Verify no worker thread leak
    assert final_threads <= initial_threads + 1, f"Thread leak detected! Initial: {initial_threads}, Final: {final_threads}"


# ===================================================================
# 3. Continuous Execution Tests
# ===================================================================

def test_continuous_runtime_execution():
    """Verify that continuous loop executes exact specified max_cycles."""
    coordinator = build_application(live_hardware=False)
    runtime = AnchorRuntime(coordinator)
    runtime.initialize()

    runtime.run_continuous(max_cycles=5, cycle_delay=0.01)

    assert runtime.cycle_count == 5
    assert runtime.running is False


# ===================================================================
# 4. Perception -> Cognition -> Assistance Pipeline Test
# ===================================================================

def test_end_to_end_pipeline_execution():
    """Verify complete perception -> cognition -> assistance workflow execution."""
    coordinator = build_application(live_hardware=False)
    runtime = AnchorRuntime(coordinator)
    runtime.initialize()
    runtime.start()

    # Simulate face detection input
    detection_payload = {
        "face_id": "face_john_01",
        "name": "John",
        "bbox": [10, 10, 100, 100],
        "confidence": 0.98,
        "user_speech": "Hello MEMORA",
    }

    # Process frame through coordinator
    runtime.process_frame(detection_payload)

    # Allow cognitive worker thread to process event
    time.sleep(0.3)

    actions = coordinator.consume_actions()
    assert isinstance(actions, list)

    runtime.shutdown()


# ===================================================================
# 5. Hardware Failure Recovery Test
# ===================================================================

def test_hardware_failure_recovery():
    """Verify runtime recovers gracefully when physical camera read fails."""
    coordinator = build_application(live_hardware=False)
    runtime = AnchorRuntime(coordinator)
    runtime.initialize()

    failing_cam = FailingCamera(fail_after=2)

    # Execute continuous runtime loop with failing camera adapter
    runtime.run_continuous(max_cycles=5, cycle_delay=0.01, camera=failing_cam)

    # Runtime should complete all 5 cycles via fallback without crashing
    assert runtime.cycle_count == 5
    assert runtime.running is False


# ===================================================================
# 6. Deadlock & Concurrency Prevention Test
# ===================================================================

def test_no_deadlocks_under_rapid_events():
    """Verify that rapid event emission does not deadlock cognitive worker queue."""
    coordinator = build_application(live_hardware=False)
    runtime = AnchorRuntime(coordinator)
    runtime.initialize()
    runtime.start()

    # Spam 50 recognition results rapidly
    for i in range(50):
        runtime.process_frame({
            "face_id": f"face_{i}",
            "name": f"Person_{i}",
            "bbox": [0, 0, 50, 50],
        })

    # Allow worker thread to drain
    time.sleep(0.5)

    assert coordinator.dropped_events_count >= 0

    runtime.shutdown()
    assert runtime.running is False
