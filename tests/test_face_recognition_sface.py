"""
OpenCV YuNet + SFace backend, exercised end to end through MemoraFaceRecognizer.process_frame
with stand-in OpenCV objects. No camera, no model files, no network: the stand-ins return
synthetic face rows and deterministic embeddings, so the tests check MEMORA's behaviour
(consent, enrolment, matching, ambiguity, deletion, unavailability), not model accuracy.
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from src.memory.database import MemoraDatabase
from src.vision import face_models
from src.vision import face_recognizer as fr

rng = np.random.default_rng(7)
PEOPLE = {pid: (lambda v: v / np.linalg.norm(v))(rng.normal(size=128).astype(np.float32)) for pid in range(1, 4)}


def face_row(person: int, x=100, y=80, size=120, score=0.95):
    """A YuNet-style row: x, y, w, h, 10 landmark coordinates, score. Landmark 0 carries the person id."""
    row = np.zeros(15, dtype=np.float32)
    row[:4] = (x, y, size, size)
    row[4] = person
    row[14] = score
    return row


class FakeYuNet:
    def __init__(self):
        self.rows = []

    def setInputSize(self, size):
        self.size = size

    def detect(self, frame):
        return 1, (np.array(self.rows, dtype=np.float32) if self.rows else None)


class FakeSFace:
    def __init__(self):
        self.feature_calls = 0
        self.mix = None  # optional (person_a, person_b) to produce an in-between face

    def alignCrop(self, frame, row):
        return int(row[4])

    def feature(self, person):
        self.feature_calls += 1
        if person == 99 and self.mix:
            v = PEOPLE[self.mix[0]] + PEOPLE[self.mix[1]]
            return (v / np.linalg.norm(v)).reshape(1, 128) * 3.0
        return PEOPLE[person].reshape(1, 128) * 5.0  # unnormalised, like the real model


@pytest.fixture
def sface(monkeypatch):
    yunet, sf = FakeYuNet(), FakeSFace()
    monkeypatch.setattr(face_models, "verify_models",
                        lambda directory=None: face_models.ModelStatus("/m/yunet.onnx", "/m/sface.onnx", []))
    monkeypatch.setattr(cv2.FaceDetectorYN, "create", staticmethod(lambda *a, **k: yunet), raising=False)
    monkeypatch.setattr(cv2.FaceRecognizerSF, "create", staticmethod(lambda *a, **k: sf), raising=False)
    return yunet, sf


FRAME = np.zeros((480, 640, 3), dtype=np.uint8)


def _recognizer(consent=True):
    rec = fr.MemoraFaceRecognizer(mock_mode=False, required_consensus_frames=1)
    rec.consent_check = lambda: consent
    return rec


def _run(rec, db, frames=1):
    out = []
    for _ in range(frames):
        out = rec.process_frame(FRAME, db)
    return out


def test_verified_models_select_the_sface_backend(sface):
    rec = _recognizer()
    assert rec.backend == "sface" and rec.unavailable_reason is None
    assert rec.tolerance == fr.settings.SFACE_MATCH_TOLERANCE


def test_without_face_consent_no_embedding_is_computed_or_stored(sface):
    yunet, sf = sface
    yunet.rows = [face_row(1)]
    db = MemoraDatabase(":memory:")
    out = _run(_recognizer(consent=False), db, frames=20)
    assert sf.feature_calls == 0
    assert out[0]["label"] == "Face recognition is off (no consent)"
    assert db.get_all_identities() == {}


def test_new_face_is_enrolled_once_then_recognised_later(sface):
    yunet, sf = sface
    yunet.rows = [face_row(1)]
    db = MemoraDatabase(":memory:")
    rec = _recognizer()
    _run(rec, db, frames=16)
    assert len(db.get_all_identities()) == 1
    first_id = next(iter(db.get_all_identities()))
    out = _run(_recognizer(), db)            # a later session sees the same person
    assert out[0]["face_id"] == first_id and len(db.get_all_identities()) == 1


def test_a_different_person_is_not_matched_to_a_stored_one(sface):
    yunet, _ = sface
    db = MemoraDatabase(":memory:")
    yunet.rows = [face_row(1)]
    _run(_recognizer(), db, frames=16)
    yunet.rows = [face_row(2)]
    out = _run(_recognizer(), db)
    assert out[0]["face_id"] is None and out[0].get("label", "").startswith("Detecting")


@pytest.mark.parametrize("row", [face_row(1, score=0.5), face_row(1, size=30)])
def test_weak_or_tiny_detections_are_ignored(sface, row):
    yunet, sf = sface
    yunet.rows = [row]
    db = MemoraDatabase(":memory:")
    assert _run(_recognizer(), db, frames=20) == []
    assert sf.feature_calls == 0 and db.get_all_identities() == {}


def test_face_resembling_two_people_is_not_named_or_enrolled(sface):
    yunet, sf = sface
    db = MemoraDatabase(":memory:")
    a = db.register_anonymous(PEOPLE[1])
    b = db.register_anonymous(PEOPLE[2])
    sf.mix = (1, 2)
    yunet.rows = [face_row(99)]
    rec = _recognizer()
    for out in (_run(rec, db) for _ in range(20)):
        assert out[0]["face_id"] is None and out[0]["label"] == "Not sure who this is"
    assert set(db.get_all_identities()) == {a, b}


def test_deleted_person_is_no_longer_recognised(sface):
    yunet, _ = sface
    db = MemoraDatabase(":memory:")
    yunet.rows = [face_row(1)]
    _run(_recognizer(), db, frames=16)
    person = next(iter(db.get_all_identities()))
    db.delete_identity(person)
    out = _run(_recognizer(), db)
    assert out[0]["face_id"] is None and db.get_all_identities() == {}


def test_revoking_consent_stops_recognition_immediately(sface):
    yunet, sf = sface
    db = MemoraDatabase(":memory:")
    yunet.rows = [face_row(1)]
    consent = {"on": True}
    rec = fr.MemoraFaceRecognizer(mock_mode=False, required_consensus_frames=1)
    rec.consent_check = lambda: consent["on"]
    _run(rec, db, frames=16)
    calls = sf.feature_calls
    consent["on"] = False
    out = _run(rec, db, frames=5)
    assert sf.feature_calls == calls and out[0]["face_id"] is None


def test_missing_models_mean_unavailable_with_a_reason(monkeypatch, tmp_path):
    monkeypatch.setenv("MEMORA_FACE_MODEL_DIR", str(tmp_path))
    monkeypatch.setattr(fr, "FACE_RECOGNITION_AVAILABLE", False)
    monkeypatch.setattr(fr, "MEDIAPIPE_AVAILABLE", False)
    rec = fr.MemoraFaceRecognizer(mock_mode=False)
    assert rec.backend == "unavailable" and "not provisioned" in rec.unavailable_reason
    assert rec.process_frame(FRAME, MemoraDatabase(":memory:")) == []


def test_model_that_opencv_cannot_load_means_unavailable(sface, monkeypatch):
    def boom(*a, **k):
        raise cv2.error("unsupported model")
    monkeypatch.setattr(cv2.FaceDetectorYN, "create", staticmethod(boom), raising=False)
    monkeypatch.setattr(fr, "FACE_RECOGNITION_AVAILABLE", False)
    monkeypatch.setattr(fr, "MEDIAPIPE_AVAILABLE", False)
    rec = fr.MemoraFaceRecognizer(mock_mode=False)
    assert rec.backend == "unavailable" and "could not be loaded" in rec.unavailable_reason


def test_checksums_gate_model_files(monkeypatch, tmp_path):
    good, bad = b"detector-bytes", b"recognizer-bytes"
    specs = (face_models.ModelFile("detector", "d.onnx", face_models.hashlib.sha256(good).hexdigest(), len(good), "MIT", "t"),
             face_models.ModelFile("recognizer", "r.onnx", "0" * 64, len(bad), "Apache-2.0", "t"))
    monkeypatch.setattr(face_models, "MODEL_FILES", specs)
    (tmp_path / "d.onnx").write_bytes(good)
    (tmp_path / "r.onnx").write_bytes(bad)
    status = face_models.verify_models(str(tmp_path))
    assert status.detector == str(tmp_path / "d.onnx") and status.recognizer is None
    assert not status.ready and "r.onnx does not match its published checksum" in status.reason()


def test_published_checksums_are_pinned():
    names = {m.filename: m.sha256 for m in face_models.MODEL_FILES}
    assert names["face_recognition_sface_2021dec.onnx"].startswith("0ba9fbfa01b5")
    assert names["face_detection_yunet_2023mar.onnx"].startswith("8f2383e4dd3c")
    assert all(len(m.sha256) == 64 for m in face_models.MODEL_FILES)


def test_provisioning_installs_only_verified_files_and_never_uses_the_network(monkeypatch, tmp_path):
    import importlib.util
    import socket
    spec = importlib.util.spec_from_file_location("prov", "deployment/provision_face_models.py")
    prov = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prov)
    good = b"yunet-bytes"
    specs = (face_models.ModelFile("detector", "d.onnx", face_models.hashlib.sha256(good).hexdigest(), len(good), "MIT", "t"),
             face_models.ModelFile("recognizer", "r.onnx", "0" * 64, 3, "Apache-2.0", "t"))
    monkeypatch.setattr(face_models, "MODEL_FILES", specs)
    monkeypatch.setattr(socket.socket, "connect", lambda *a: pytest.fail("network used"))
    src, dest = tmp_path / "downloads", tmp_path / "models"
    src.mkdir()
    (src / "d.onnx").write_bytes(good)
    assert prov.provision(str(src), str(dest)) == [str(dest / "d.onnx")]
    (src / "r.onnx").write_bytes(b"bad")
    with pytest.raises(SystemExit, match="r.onnx"):
        prov.provision(str(src), str(dest))
    assert sorted(p.name for p in dest.iterdir()) == ["d.onnx"]


def test_check_reports_face_model_status(monkeypatch, tmp_path):
    from src.operations.startup_validator import StartupValidator
    monkeypatch.setenv("MEMORA_FACE_MODEL_DIR", str(tmp_path))
    item = StartupValidator().check_face_models()
    assert item.status == "WARNING" and "not provisioned" in item.message
