"""
Unit tests for the Samsung Anchor Runtime.
"""

import pytest

from src.runtime.runtime import AnchorRuntime


# ==========================================================
# Fake Coordinator
# ==========================================================

class FakeCoordinator:
    def __init__(self):
        self.initialized = False
        self.started = False
        self.stopped = False
        self.last_frame = None

    def initialize(self):
        self.initialized = True

    def start(self):
        self.started = True

    def shutdown(self):
        self.stopped = True

    def process_frame(self, frame):
        self.last_frame = frame
        return frame


# ==========================================================
# Fake Camera
# ==========================================================

class FakeCamera:
    def __init__(self, success=True):
        self.success = success
        self.frame = object()

    def read(self):
        return self.success, self.frame


# ==========================================================
# Factory
# ==========================================================

def create_runtime():
    coordinator = FakeCoordinator()
    runtime = AnchorRuntime(coordinator)
    return runtime, coordinator


# ==========================================================
# Tests
# ==========================================================

def test_initialize():
    runtime, coordinator = create_runtime()

    runtime.initialize()

    assert runtime.running is False
    assert coordinator.initialized is True


def test_start():
    runtime, coordinator = create_runtime()

    runtime.start()

    assert runtime.running is True
    assert coordinator.started is True


def test_shutdown():
    runtime, coordinator = create_runtime()

    runtime.start()
    runtime.shutdown()

    assert runtime.running is False
    assert coordinator.stopped is True


def test_runtime_stores_coordinator():
    runtime, coordinator = create_runtime()

    assert runtime.coordinator is coordinator


def test_runtime_initial_state():
    runtime, _ = create_runtime()

    assert runtime.running is False


def test_process_frame():
    runtime, coordinator = create_runtime()

    frame = object()

    result = runtime.process_frame(frame)

    assert coordinator.last_frame is frame
    assert result is frame


def test_process_single_frame():
    runtime, coordinator = create_runtime()

    camera = FakeCamera()

    frame, results = runtime.process_single_frame(camera)

    assert frame is camera.frame
    assert results is camera.frame
    assert coordinator.last_frame is camera.frame


def test_process_single_frame_failure():
    runtime, _ = create_runtime()

    camera = FakeCamera(success=False)

    with pytest.raises(RuntimeError):
        runtime.process_single_frame(camera)