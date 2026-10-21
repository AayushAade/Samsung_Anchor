"""Schema migrations are additive, idempotent, and preserve existing data."""

from __future__ import annotations

import shutil
import sqlite3

import pytest

from src.memory.database import MemoraDatabase
from src.memory.migrations import LATEST_VERSION


def _old_schema_db(path):
    """A database with the pre-migration objects/object_history tables and data."""
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE system_state (key VARCHAR PRIMARY KEY, value VARCHAR);
        CREATE TABLE objects (name VARCHAR PRIMARY KEY, last_seen VARCHAR, x FLOAT, y FLOAT, room VARCHAR, bounding_box JSON);
        CREATE TABLE object_history (id INTEGER PRIMARY KEY, object_name VARCHAR, timestamp VARCHAR, x FLOAT, y FLOAT, room VARCHAR, bounding_box JSON);
        INSERT INTO objects VALUES ('keys', '2026-01-01T10:00:00', 1, 2, 'Hall', NULL);
        INSERT INTO object_history VALUES (1, 'keys', '2026-01-01T10:00:00', 1, 2, 'Hall', NULL);
    """)
    con.commit()
    con.close()


def test_upgrade_from_old_schema_keeps_data(tmp_path):
    path = tmp_path / "old_v2.sqlite"
    _old_schema_db(str(path))
    db = MemoraDatabase(str(path))
    assert db.migrations_applied == ["object sighting source"]
    info = db.get_last_known_location("keys")
    assert info["room"] == "Hall" and info["source"] is None
    assert db._get_system_state("schema_version") == str(LATEST_VERSION)
    db.close()
    again = MemoraDatabase(str(path))
    assert again.migrations_applied == []  # idempotent


def test_fresh_database_is_at_latest_version(tmp_path):
    db = MemoraDatabase(str(tmp_path / "fresh.sqlite"))
    assert db._get_system_state("schema_version") == str(LATEST_VERSION)


def test_newer_schema_is_refused_without_changes(tmp_path):
    path = tmp_path / "future_v2.sqlite"
    MemoraDatabase(str(path))._set_system_state("schema_version", "999")
    before = path.read_bytes()
    with pytest.raises(RuntimeError, match="newer than this MEMORA build"):
        MemoraDatabase(str(path))
    assert path.read_bytes() == before


def test_migration_on_copy_of_real_database_if_present(tmp_path):
    import os
    real = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memora_db_v2.sqlite")
    if not os.path.exists(real):
        pytest.skip("no local database to copy")
    copy = tmp_path / "copy_v2.sqlite"
    shutil.copy2(real, copy)
    counts = lambda p: {t: sqlite3.connect(p).execute(f'select count(*) from "{t}"').fetchone()[0]
                        for t in ("objects", "object_history", "episodes", "identities", "relevant_memories")}
    before = counts(str(copy))
    MemoraDatabase(str(copy))
    assert counts(str(copy)) == before
