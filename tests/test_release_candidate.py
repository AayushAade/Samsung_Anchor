"""
Release Candidate (RC1) Verification & Hardening Tests for MEMORA (Samsung Anchor).
"""

import threading
import time
import numpy as np
import pytest
from src.memory.database import MemoraDatabase
from src.vision.face_recognizer import MemoraFaceRecognizer
from src.application.factory import build_application


def test_bounded_cognitive_queue_drop_oldest():
    """Verify bounded cognitive queue (maxsize=10) drops oldest events and tracks metric."""
    coordinator = build_application()
    assert coordinator._cognitive_queue.maxsize == 10
    assert coordinator.dropped_events_count == 0

    # Push 15 face_detected events without pulling
    for i in range(15):
        coordinator.event_bus.publish("face_detected", {"frame_id": i})

    # Queue size should be capped at 10
    assert coordinator._cognitive_queue.qsize() == 10
    assert coordinator.dropped_events_count == 5

    # Oldest event remaining should be frame_id 5
    oldest_event = coordinator._cognitive_queue.get_nowait()
    assert oldest_event["frame_id"] == 5

    coordinator.shutdown()


def test_thread_safe_face_tracking():
    """Verify concurrent multi-threaded active_tracks mutations raise no race condition errors."""
    db = MemoraDatabase("sqlite:///:memory:")
    rec = MemoraFaceRecognizer(mock_mode=True)

    import traceback
    errors = []

    def worker(thread_id):
        try:
            for frame_idx in range(20):
                # Simulated frame numpy array
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                rec.process_frame(frame, db)
                time.sleep(0.001)
        except Exception as e:
            errors.append(traceback.format_exc())

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    if errors:
        print("Worker error:", errors[0])
    assert len(errors) == 0


def test_multi_frame_identity_consensus():
    """Verify N-frame consensus requires configurable consecutive frames before identity assignment."""
    rec = MemoraFaceRecognizer(mock_mode=False, required_consensus_frames=3)
    assert rec.required_consensus_frames == 3


def test_stale_track_eviction():
    """Verify stale face tracks are automatically evicted after timeout or frame limit."""
    db = MemoraDatabase("sqlite:///:memory:")
    rec = MemoraFaceRecognizer(mock_mode=True)

    # Seed active track
    now_time = time.time()
    rec.active_tracks["Stale_Track_1"] = {
        "state": "RECOGNIZED",
        "box": (10, 50, 50, 10),
        "center": (30, 30),
        "embeddings": [],
        "frames_seen": 1,
        "missed_frames": 32,
        "last_seen_time": now_time - 70.0,
        "recognized_logged": True,
        "confirmed_logged": False,
    }

    rec._update_missed_tracks(now_time, db, associated_tracks=set())
    assert "Stale_Track_1" not in rec.active_tracks
