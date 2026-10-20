"""
Consent is enforced in the running product, not only displayed.
"""

from __future__ import annotations

import contextlib
import io

import numpy as np

from src.application.factory import build_application
from src.clinical.clinical_models import ConsentFeature
from src.clinical.consent_manager import ConsentManager
from src.memory.database import MemoraDatabase
from tests.consent_helpers import allow_faces, allow_memory


def _frames(coord, n=40):
    frame = np.full((480, 640, 3), 120, dtype=np.uint8)
    with contextlib.redirect_stdout(io.StringIO()):
        return [coord.process_frame(frame) for _ in range(n)]


def test_no_face_data_stored_without_biometric_consent():
    db = MemoraDatabase(":memory:")
    coord = build_application(live_hardware=False, database=db)
    results = _frames(coord)
    assert db.identity_repo.get_all() == [] and len(db.vector_store) == 0
    assert all(r.get("face_id") is None for res in results for r in (res if isinstance(res, list) else [res]))


def test_face_data_stored_only_after_consent():
    db = MemoraDatabase(":memory:")
    coord = build_application(live_hardware=False, database=db)
    allow_faces(coord.pipeline)
    _frames(coord)
    assert len(db.identity_repo.get_all()) >= 1 and len(db.vector_store) >= 1


def test_episodes_not_logged_without_memory_consent():
    db = MemoraDatabase(":memory:")
    coord = build_application(live_hardware=False, database=db)
    coord.pipeline.process(user_speech="What time is it?")
    assert db.episode_repo.count() == 0
    allow_memory(coord.pipeline)
    coord.pipeline.process(user_speech="What time is it?")
    assert db.episode_repo.count() == 1


def test_consent_persists_and_distinguishes_never_asked(tmp_path):
    db = MemoraDatabase(str(tmp_path / "c.sqlite"))
    mgr = ConsentManager(db)
    assert not mgr.has_decided(ConsentFeature.CONVERSATION_STORAGE)
    mgr.update_consent(ConsentFeature.CONVERSATION_STORAGE, False)
    again = ConsentManager(MemoraDatabase(str(tmp_path / "c.sqlite")))
    assert again.has_decided(ConsentFeature.CONVERSATION_STORAGE)
    assert again.is_consent_granted(ConsentFeature.CONVERSATION_STORAGE) is False
