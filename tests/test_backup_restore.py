"""Backup/restore keeps data consistent, detects tampering, and never loses the current state."""

from __future__ import annotations

import json
import os

import numpy as np
import pytest

from src.cognition.conversational_memory import ConversationalMemory
from src.memory.backup import BackupError, create_backup, restore_backup, verify_backup
from src.memory.database import MemoraDatabase


def _db_with_data(path):
    db = MemoraDatabase(path)
    db.register_anonymous(np.ones(128, dtype=np.float32) / np.sqrt(128))
    ConversationalMemory(db).respond("My daughter is Riya")
    return db


def test_backup_restore_round_trip(tmp_path):
    path = str(tmp_path / "live.sqlite")
    db = _db_with_data(path)
    backup = create_backup(db.db_path, str(tmp_path / "b"))
    assert verify_backup(backup)["integrity"]["ok"]

    ConversationalMemory(db).respond("My daughter's name is Priya")
    db.delete_identity("Anonymous_ID_1")
    db.close()

    result = restore_backup(backup, MemoraDatabase(path).db_path)
    assert result["pre_restore_backup"] and os.path.isdir(result["pre_restore_backup"])
    assert os.listdir(result["pre_restore_backup"])  # raw copies of the replaced files
    restored = MemoraDatabase(path)
    assert "Riya" in ConversationalMemory(restored).respond("Who is my daughter?")
    assert restored.check_integrity()["ok"] and len(restored.vector_store) == 1
    for name in os.listdir(backup):
        assert oct(os.stat(os.path.join(backup, name)).st_mode & 0o777) == "0o600"


def test_tampered_backup_is_rejected_and_live_data_untouched(tmp_path):
    path = str(tmp_path / "live.sqlite")
    db = _db_with_data(path)
    backup = create_backup(db.db_path, str(tmp_path / "b"))
    with open(os.path.join(backup, os.path.basename(db.db_path)), "ab") as f:
        f.write(b"garbage")
    before = open(db.db_path, "rb").read()
    with pytest.raises(BackupError):
        restore_backup(backup, db.db_path)
    assert open(db.db_path, "rb").read() == before


def test_manifest_records_row_counts(tmp_path):
    db = _db_with_data(str(tmp_path / "live.sqlite"))
    backup = create_backup(db.db_path, str(tmp_path / "b"))
    manifest = json.load(open(os.path.join(backup, "manifest.json")))
    assert manifest["row_counts"]["identities"] == 1
    assert manifest["row_counts"]["relevant_memories"] == 1


def test_restore_works_when_live_database_is_corrupt(tmp_path):
    db = _db_with_data(str(tmp_path / "live.sqlite"))
    backup = create_backup(db.db_path, str(tmp_path / "b"))
    path = db.db_path
    db.close()
    with open(path, "wb") as f:
        f.write(b"not a database")
    result = restore_backup(backup, path)
    pre = result["pre_restore_backup"]
    assert open(os.path.join(pre, os.path.basename(path)), "rb").read() == b"not a database"
    assert "Riya" in ConversationalMemory(MemoraDatabase(path)).respond("Who is my daughter?")
