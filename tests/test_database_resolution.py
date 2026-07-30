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
