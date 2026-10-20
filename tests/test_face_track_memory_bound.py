"""A face that stays in view must not make memory or per-frame work grow without bound."""

from __future__ import annotations

import io
import contextlib

import numpy as np

from src.memory.database import MemoraDatabase
from src.vision.face_recognizer import TRACK_EMBEDDING_WINDOW, MemoraFaceRecognizer


def test_track_embedding_history_is_bounded():
    rec = MemoraFaceRecognizer(mock_mode=True)
    db = MemoraDatabase(":memory:")
    frame = np.full((480, 640, 3), 120, dtype=np.uint8)
    with contextlib.redirect_stdout(io.StringIO()):
        for _ in range(TRACK_EMBEDDING_WINDOW * 4):
            rec.process_frame(frame, db)
    assert rec.active_tracks, "the synthetic face should be tracked"
    for track in rec.active_tracks.values():
        assert len(track["embeddings"]) <= TRACK_EMBEDDING_WINDOW
