"""
Data isolation, persistence, and integrity guarantees for identity storage.

These cover defects where every database shared one face-embedding file in the
repository root, so test/demo databases could overwrite or delete real data.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pytest

from src.memory.database import MemoraDatabase, vector_store_paths
from src.memory.vector_store import FaissVectorStore, VectorStoreError


def _vec(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.normal(size=128).astype(np.float32)
    return v / np.linalg.norm(v)


def test_in_memory_database_never_touches_filesystem(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    db = MemoraDatabase(":memory:")
    db.register_anonymous(_vec(1))
    db.clear()
    assert db.vector_store.persistent is False
    assert os.listdir(tmp_path) == []


def test_each_database_has_its_own_embedding_files(tmp_path):
    a = MemoraDatabase(str(tmp_path / "a.sqlite"))
    b = MemoraDatabase(str(tmp_path / "b.sqlite"))
    a_id = a.register_anonymous(_vec(1))

    assert a.vector_store.mapping_path != b.vector_store.mapping_path
    assert len(b.vector_store) == 0

    # Clearing one database must not delete another database's embeddings.
    b.clear()
    reopened = MemoraDatabase(str(tmp_path / "a.sqlite"))
    match_id, _, _ = reopened.find_match(_vec(1), tolerance=0.5)
    assert match_id == a_id


def test_embeddings_survive_restart_and_integrity_is_ok(tmp_path):
    path = str(tmp_path / "persist.sqlite")
    db = MemoraDatabase(path)
    ident = db.register_anonymous(_vec(7))
    db.close()

    db2 = MemoraDatabase(path)
    match_id, _, dist = db2.find_match(_vec(7), tolerance=0.5)
    assert match_id == ident and dist < 1e-3
    report = db2.check_integrity()
    assert report["ok"], report


def test_integrity_detects_identity_without_embeddings(tmp_path):
    path = str(tmp_path / "split.sqlite")
    db = MemoraDatabase(path)
    db.register_anonymous(_vec(3))
    db.close()
    _, mapping = vector_store_paths(db.db_path)
    os.remove(mapping)

    report = MemoraDatabase(path).check_integrity()
    assert report["ok"] is False
    assert report["identities_without_embeddings"] == ["Anonymous_ID_1"]


def test_corrupt_mapping_is_quarantined_not_overwritten(tmp_path):
    path = str(tmp_path / "corrupt.sqlite")
    db = MemoraDatabase(path)
    db.register_anonymous(_vec(4))
    db.close()
    _, mapping = vector_store_paths(db.db_path)
    with open(mapping, "w") as f:
        f.write("{not json")

    db2 = MemoraDatabase(path)
    report = db2.check_integrity()
    assert report["vector_store_load_error"]
    assert report["ok"] is False
    quarantined = [p for p in os.listdir(tmp_path) if ".corrupt-" in p]
    assert quarantined, "corrupt file should be preserved for recovery"
    with open(tmp_path / next(p for p in quarantined if ".faces.json." in p)) as f:
        assert f.read() == "{not json"


def test_wrong_dimension_embedding_is_rejected_without_partial_identity():
    db = MemoraDatabase(":memory:")
    with pytest.raises(VectorStoreError):
        db.register_anonymous(np.ones(64))
    assert db.identity_repo.get_all() == []


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0,
                    reason="root ignores directory permissions, so a write failure cannot be induced this way")
def test_failed_persist_rolls_back(tmp_path):
    store = FaissVectorStore(str(tmp_path / "x.index"), str(tmp_path / "x.json"))
    store.add_embedding("ok", _vec(1))
    os.chmod(tmp_path, 0o500)
    try:
        with pytest.raises(VectorStoreError):
            store.add_embedding("fails", _vec(2))
    finally:
        os.chmod(tmp_path, 0o700)
    assert store.identity_ids() == {"ok"}
    assert store.index.ntotal == 1


def test_delete_identity_removes_record_and_embeddings(tmp_path):
    path = str(tmp_path / "del.sqlite")
    db = MemoraDatabase(path)
    keep = db.register_anonymous(_vec(10))
    gone = db.register_anonymous(_vec(11))

    report = db.delete_identity(gone)
    assert report == {"identity_id": gone, "record_deleted": True, "embeddings_deleted": 1}

    db2 = MemoraDatabase(path)
    assert db2.find_match(_vec(11), tolerance=0.5)[0] is None
    assert db2.find_match(_vec(10), tolerance=0.5)[0] == keep
    assert db2.check_integrity()["ok"]


def test_legacy_files_are_adopted_read_only_for_default_db(tmp_path, monkeypatch):
    from config import settings

    db_file = tmp_path / "memora_db.sqlite"
    monkeypatch.setattr(settings, "DB_PATH", str(db_file))
    legacy_map = tmp_path / "face_mapping.json"
    legacy_map.write_text(json.dumps({
        "id_mapping": {"0": "Anonymous_ID_1"},
        "embeddings_cache": {"0": _vec(5).tolist()},
        "next_id": 1,
    }))
    before = legacy_map.read_text()

    db = MemoraDatabase()
    assert db.vector_store.loaded_from == str(legacy_map)
    assert db.vector_store.find_match(_vec(5), 0.5)[0] == "Anonymous_ID_1"
    assert legacy_map.read_text() == before


def test_personal_data_files_are_owner_only(tmp_path):
    path = str(tmp_path / "perm.sqlite")
    db = MemoraDatabase(path)
    db.register_anonymous(_vec(21))
    index_path, mapping_path = vector_store_paths(db.db_path)
    for p in (db.db_path, index_path, mapping_path):
        assert oct(os.stat(p).st_mode & 0o777) == "0o600", p
