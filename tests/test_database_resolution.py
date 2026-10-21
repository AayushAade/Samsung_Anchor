"""
Unit and Integration Tests for MemoraDatabase Path Resolution and Hardening (Phase 17.1).
"""

import os
import pytest
from src.memory.database import MemoraDatabase, resolve_db_url


def test_resolve_db_url_filesystem_path():
    """Verify filesystem path resolution appends _v2.sqlite correctly."""
    url, fs_path = resolve_db_url("memora_db.sqlite")
    assert url == "sqlite:///memora_db_v2.sqlite"
    assert fs_path == "memora_db_v2.sqlite"

    url_v2, fs_path_v2 = resolve_db_url("memora_db_v2.sqlite")
    assert url_v2 == "sqlite:///memora_db_v2.sqlite"
    assert fs_path_v2 == "memora_db_v2.sqlite"


def test_resolve_db_url_in_memory():
    """Verify sqlite:///:memory: and :memory: resolve to in-memory URL with no filesystem path."""
    url1, fs1 = resolve_db_url("sqlite:///:memory:")
    assert url1 == "sqlite:///:memory:"
    assert fs1 is None

    url2, fs2 = resolve_db_url(":memory:")
    assert url2 == "sqlite:///:memory:"
    assert fs2 is None


def test_in_memory_database_creates_no_filesystem_artifact():
    """Verify initializing MemoraDatabase with sqlite:///:memory: does not create sqlite:/:memory: file artifact."""
    artifact_dir = "sqlite:"
    artifact_file = "sqlite:/:memory:"
    
    if os.path.exists(artifact_file):
        os.remove(artifact_file)
    if os.path.exists(artifact_dir):
        import shutil
        shutil.rmtree(artifact_dir, ignore_errors=True)

    with MemoraDatabase("sqlite:///:memory:") as db:
        assert db.db_url == "sqlite:///:memory:"
        assert db.db_path is None
        # Basic DB operation
        db.set_current_room("Living Room")
        assert db.get_current_room() == "Living Room"

    # Confirm no artifact created on disk
    assert not os.path.exists(artifact_file)
    assert not os.path.exists(artifact_dir)


def test_context_manager_and_close():
    """Verify context manager support (__enter__ and __exit__) disposes engine correctly."""
    with MemoraDatabase("sqlite:///:memory:") as db:
        assert db.get_current_room() == "Living Room"
        db.clear()
        assert db.get_current_room() == "Living Room"


def test_check_names_the_file_actually_used_when_it_is_damaged(tmp_path, monkeypatch):
    """Found by the end-to-end journey: --check named memora.sqlite while the damaged file was memora_v2.sqlite."""
    from config import settings
    from src.operations.startup_validator import StartupValidator
    (tmp_path / "memora_v2.sqlite").write_bytes(b"\0" * 4096)
    monkeypatch.setattr(settings, "DB_PATH", str(tmp_path / "memora.sqlite"))
    item = StartupValidator().check_user_database()
    assert item.status == "FAIL" and str(tmp_path / "memora_v2.sqlite") in item.message


def test_check_never_modifies_or_creates_the_user_database(tmp_path, monkeypatch):
    """Found when a bare --check migrated a pre-existing database: diagnostics must be read-only."""
    import hashlib
    import sqlite3
    from config import settings
    from src.operations.startup_validator import StartupValidator
    legacy = tmp_path / "legacy_v2.sqlite"
    con = sqlite3.connect(legacy)  # an old-schema database: no schema_version, no 'source' columns
    con.executescript("create table system_state (key varchar primary key, value varchar);"
                      "create table objects (name varchar primary key, room varchar, last_seen varchar);"
                      "insert into objects values ('keys', 'Kitchen', '2026-09-29T10:00:00');")
    con.commit()
    con.close()
    os.chmod(legacy, 0o644)
    before = (hashlib.sha256(legacy.read_bytes()).hexdigest(), os.stat(legacy).st_mtime_ns, os.stat(legacy).st_mode)
    monkeypatch.setattr(settings, "DB_PATH", str(legacy))
    item = StartupValidator().check_user_database()
    assert item.status in ("PASS", "WARNING"), item.message
    after = (hashlib.sha256(legacy.read_bytes()).hexdigest(), os.stat(legacy).st_mtime_ns, os.stat(legacy).st_mode)
    assert after == before
    assert sorted(os.listdir(tmp_path)) == ["legacy_v2.sqlite"]

    missing = tmp_path / "new" / "memora.sqlite"
    monkeypatch.setattr(settings, "DB_PATH", str(missing))
    item = StartupValidator().check_user_database()
    assert item.status == "PASS" and "no database yet" in item.message
    assert not (tmp_path / "new").exists()
